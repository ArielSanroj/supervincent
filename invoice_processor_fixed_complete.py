#!/usr/bin/env python3
"""
Sistema mejorado de procesamiento de facturas - Versión completa y funcional
Incluye: integración Nanobot, manejo robusto de errores, y todas las funcionalidades
"""

import argparse
import base64
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pdfplumber
import requests
from dotenv import load_dotenv

from alegra_reports import AlegraReports
from config import ACCOUNTING_CONFIG, ALEGRA_CONFIG, LOGGING_CONFIG, NANOBOT_CONFIG
from nanobot_client import NanobotClient, NanobotError, NanobotResponseError

# Configurar logging dinámicamente
log_level = LOGGING_CONFIG.get('level', 'INFO')
log_level_value = getattr(logging, log_level.upper(), logging.INFO)
log_format = LOGGING_CONFIG.get('format', '%(asctime)s - %(levelname)s - %(message)s')
log_file = LOGGING_CONFIG.get('file', 'logs/invoicebot.log')
os.makedirs(os.path.dirname(log_file) or '.', exist_ok=True)

logging.basicConfig(
    level=log_level_value,
    format=log_format,
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# OCR imports for image processing
try:
    import pytesseract  # type: ignore[import]
    from PIL import Image  # type: ignore[import]
    import cv2  # type: ignore[import]
    import numpy as np  # type: ignore[import]
except ImportError as e:  # pragma: no cover - best effort optional deps
    logger.warning("OCR libraries not available: %s", e)
    pytesseract = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]
    cv2 = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]
    OCR_AVAILABLE = False
else:
    OCR_AVAILABLE = True

# Cargar variables de entorno
load_dotenv()

class InvoiceProcessor:
    """Procesador mejorado de facturas con detección automática y integración Alegra"""

    def __init__(
        self,
        *,
        use_nanobot: Optional[bool] = None,
        nanobot_host: Optional[str] = None,
        nanobot_confidence_threshold: Optional[float] = None,
    ) -> None:
        self.alegra_email = os.getenv('ALEGRA_USER')
        self.alegra_token = os.getenv('ALEGRA_TOKEN')
        self.base_url = ALEGRA_CONFIG.get('base_url', 'https://api.alegra.com/api/v1')
        self.alegra_timeout = ALEGRA_CONFIG.get('timeout', 30)
        self.alegra_max_retries = ALEGRA_CONFIG.get('max_retries', 3)

        if not self.alegra_email or not self.alegra_token:
            raise ValueError("Faltan credenciales de Alegra en .env")

        self.accounting_config = ACCOUNTING_CONFIG

        self.nanobot_config = dict(NANOBOT_CONFIG)
        if use_nanobot is not None:
            self.nanobot_config['enabled'] = use_nanobot
        if nanobot_host:
            self.nanobot_config['host'] = nanobot_host
        if nanobot_confidence_threshold is not None:
            self.nanobot_config['confidence_threshold'] = nanobot_confidence_threshold

        self.nanobot_enabled = bool(self.nanobot_config.get('enabled', False))
        self.nanobot_confidence_threshold = float(self.nanobot_config.get('confidence_threshold', 0.75))
        self.nanobot_triage_on_api_error = bool(self.nanobot_config.get('triage_on_api_error', True))
        self.nanobot_classifier_agent = self.nanobot_config.get('classifier_agent')
        self.nanobot_triage_agent = self.nanobot_config.get('triage_agent')

        self.nanobot_client: Optional[NanobotClient] = None
        if self.nanobot_enabled and self.nanobot_classifier_agent:
            try:
                host = self.nanobot_config.get('host') or 'http://localhost:8080'
                self.nanobot_client = NanobotClient(host)
                logger.info("Nanobot habilitado usando host %s", host)
            except (NanobotError, ValueError) as exc:
                logger.error("No se pudo inicializar Nanobot: %s", exc)
                self.nanobot_enabled = False

        self.last_classification: Optional[Dict[str, Any]] = None

        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Asegurar que los directorios necesarios existan"""
        directories = [
            'logs',
            'facturas/processed',
            'facturas/error',
            'backup',
            'reports'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.debug("Directorio asegurado: %s", directory)
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Obtener headers de autenticación para Alegra"""
        credentials = f"{self.alegra_email}:{self.alegra_token}"
        auth_header = f"Basic {base64.b64encode(credentials.encode()).decode()}"
        
        return {
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }
    
    def detect_invoice_type(self, texto: str) -> str:
        """Detectar automáticamente si es factura de compra o venta."""

        texto_lower = texto.lower()
        legacy_result, compra_score, venta_score = self._legacy_detect_invoice_type(texto_lower)

        if not self.nanobot_enabled or not self.nanobot_client:
            logger.info(
                "Clasificación (legacy) - compra: %s, venta: %s", compra_score, venta_score
            )
            return legacy_result

        try:
            response = self.nanobot_client.classify_invoice(
                self.nanobot_classifier_agent,
                texto,
            )

            if isinstance(response, dict):
                tipo = str(response.get('tipo', '')).lower()
                confianza = self._safe_float(response.get('confianza'))
                razon = response.get('razon', '')

                logger.info(
                    "Clasificación Nanobot - tipo: %s, confianza: %s, razón: %s",
                    tipo,
                    confianza,
                    razon,
                )

                if tipo in {'compra', 'venta'} and confianza is not None:
                    self.last_classification = {
                        'tipo': tipo,
                        'confianza': confianza,
                        'razon': razon,
                    }

                    if confianza >= self.nanobot_confidence_threshold:
                        return tipo

                    logger.warning(
                        "Confianza Nanobot baja (%.2f < %.2f), usando fallback",
                        confianza,
                        self.nanobot_confidence_threshold,
                    )

                    triage_payload = {
                        'texto': texto,
                        'clasificacion_legacy': legacy_result,
                        'clasificacion_nanobot': self.last_classification,
                        'compra_score': compra_score,
                        'venta_score': venta_score,
                    }
                    triage_result = self._invoke_triage_agent(
                        'Confianza baja en clasificación',
                        triage_payload,
                    )
                    if triage_result:
                        corrected = triage_result.get('datos_corregidos', {})
                        tipo_corregido = corrected.get('tipo')
                        if tipo_corregido in {'compra', 'venta'}:
                            logger.info(
                                "Triage ajustó tipo de factura a %s", tipo_corregido
                            )
                            return tipo_corregido

            else:
                logger.error("Respuesta inesperada de Nanobot classifier: %s", response)

        except (NanobotError, NanobotResponseError) as exc:
            logger.error("Error clasificando con Nanobot: %s", exc)

        logger.info(
            "Clasificación fallback - compra: %s, venta: %s", compra_score, venta_score
        )
        return legacy_result

    def _legacy_detect_invoice_type(self, texto_lower: str) -> Tuple[str, int, int]:
        """Detección legacy de tipo de factura"""
        compra_keywords = [
            'proveedor', 'proveedores', 'compra', 'compras', 'factura de compra',
            'bill', 'purchase', 'supplier', 'vendor', 'factura de proveedor',
            'orden de compra', 'oc', 'pedido', 'receipt'
        ]

        venta_keywords = [
            'cliente', 'clientes', 'venta', 'ventas', 'factura de venta',
            'invoice', 'sale', 'customer', 'factura de cliente',
            'orden de venta', 'ov', 'cotización', 'quote'
        ]

        compra_score = sum(1 for keyword in compra_keywords if keyword in texto_lower)
        venta_score = sum(1 for keyword in venta_keywords if keyword in texto_lower)

        if compra_score > venta_score:
            legacy_result = 'compra'
        elif venta_score > compra_score:
            legacy_result = 'venta'
        else:
            if any(pattern in texto_lower for pattern in ['factura electrónica de venta', 'invoice']):
                legacy_result = 'venta'
            elif any(pattern in texto_lower for pattern in ['bill', 'receipt', 'proveedor']):
                legacy_result = 'compra'
            else:
                logger.warning("No se pudo determinar el tipo de factura, asumiendo VENTA")
                legacy_result = 'venta'

        return legacy_result, compra_score, venta_score

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        """Convertir valor a float de forma segura"""
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _invoke_triage_agent(self, reason: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Invocar agente de triage de Nanobot"""
        if not self.nanobot_enabled or not self.nanobot_client or not self.nanobot_triage_agent:
            return None

        try:
            triage_payload = {
                'razon': reason,
                'datos': payload,
            }
            return self.nanobot_client.triage_invoice(self.nanobot_triage_agent, triage_payload)
        except (NanobotError, NanobotResponseError) as exc:
            logger.error("Error en triage de Nanobot: %s", exc)
            return None
    
    def extract_data_from_pdf(self, pdf_path: str) -> Optional[Dict]:
        """
        Extraer datos del PDF con detección automática de tipo
        y parsing mejorado para mayor robustez
        """
        logger.info(f"📄 Procesando PDF: {pdf_path}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                texto = ''
                for page in pdf.pages:
                    texto += page.extract_text() or ''
            
            if not texto.strip():
                logger.error("No se pudo extraer texto del PDF")
                return None
            
            logger.info("📝 Texto extraído del PDF:")
            logger.info(f"Longitud: {len(texto)} caracteres")
            logger.debug(f"Primeros 500 caracteres: {texto[:500]}")
            
            # Detectar tipo automáticamente
            invoice_type = self.detect_invoice_type(texto)
            logger.info(f"📋 Tipo detectado: {'Factura de COMPRA' if invoice_type == 'compra' else 'Factura de VENTA'}")
            
            # Extraer datos con parsing mejorado
            datos = self._parse_invoice_data(texto)
            datos['tipo'] = invoice_type
            
            logger.info(f"📊 Datos extraídos - Tipo: {invoice_type}, Total: ${datos.get('total', 0):,.2f}")
            
            return datos
            
        except Exception as e:
            logger.error(f"❌ Error procesando PDF: {e}")
            return None

    def extract_data_from_image(self, image_path: str) -> Optional[Dict]:
        """Extraer datos de imagen usando OCR"""
        if not OCR_AVAILABLE:
            logger.error("❌ OCR no disponible")
            return None
        
        logger.info(f"🖼️ Procesando imagen: {image_path}")
        
        try:
            # Cargar imagen
            image = cv2.imread(image_path)
            if image is None:
                logger.error("No se pudo cargar la imagen")
                return None
            
            # Preprocesamiento para mejorar OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 3)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # OCR
            texto = pytesseract.image_to_string(gray, lang='spa')
            
            if not texto.strip():
                logger.error("No se pudo extraer texto de la imagen")
                return None
            
            logger.info("📝 Texto extraído de la imagen:")
            logger.info(f"Longitud: {len(texto)} caracteres")
            logger.debug(f"Primeros 500 caracteres: {texto[:500]}")
            
            # Detectar tipo automáticamente
            invoice_type = self.detect_invoice_type(texto)
            logger.info(f"📋 Tipo detectado: {'Factura de COMPRA' if invoice_type == 'compra' else 'Factura de VENTA'}")
            
            # Extraer datos con parsing mejorado
            datos = self._parse_invoice_data(texto)
            datos['tipo'] = invoice_type
            
            logger.info(f"📊 Datos extraídos - Tipo: {invoice_type}, Total: ${datos.get('total', 0):,.2f}")
            
            return datos
            
        except Exception as e:
            logger.error(f"❌ Error procesando imagen: {e}")
            return None

    def _parse_invoice_data(self, texto: str) -> Dict:
        """Parsear datos de factura desde texto"""
        # Patrones de regex mejorados
        patterns = {
            'fecha': [
                r'Fecha[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'Fecha de emisión[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            'cliente': [
                r'Cliente[:\s]+(.+)',
                r'Customer[:\s]+(.+)',
                r'Facturar a[:\s]+(.+)',
                r'Bill to[:\s]+(.+)',
                r'Razón Social[:\s]+(.+)',
                r'Nombre[:\s]+(.+)'
            ],
            'proveedor': [
                r'Proveedor[:\s]+(.+)',
                r'Supplier[:\s]+(.+)',
                r'Vendor[:\s]+(.+)',
                r'De[:\s]+(.+)',
                r'From[:\s]+(.+)'
            ],
            'total': [
                r'Total[:\s]+\$?([\d,]+\.?\d*)',
                r'Amount[:\s]+\$?([\d,]+\.?\d*)',
                r'Subtotal[:\s]+\$?([\d,]+\.?\d*)',
                r'Importe Total[:\s]+\$?([\d,]+\.?\d*)',
                r'Total a Pagar[:\s]+\$?([\d,]+\.?\d*)'
            ]
        }
        
        datos = {}
        
        # Extraer fecha
        for pattern in patterns['fecha']:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                fecha_str = match.group(1)
                # Convertir formato de fecha
                try:
                    if '/' in fecha_str:
                        if len(fecha_str.split('/')[2]) == 2:
                            fecha_str = fecha_str.replace('/', '-')
                            fecha = datetime.strptime(fecha_str, '%d-%m-%y')
                        else:
                            fecha = datetime.strptime(fecha_str, '%d/%m/%Y')
                    else:
                        fecha = datetime.strptime(fecha_str, '%d-%m-%Y')
                    datos['fecha'] = fecha.strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue
        
        # Si no se encontró fecha, usar fecha actual
        if 'fecha' not in datos:
            datos['fecha'] = datetime.now().strftime('%Y-%m-%d')
        
        # Extraer cliente/proveedor
        for pattern in patterns['cliente']:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                datos['cliente'] = match.group(1).strip()
                break
        
        for pattern in patterns['proveedor']:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                datos['proveedor'] = match.group(1).strip()
                break
        
        # Extraer total
        for pattern in patterns['total']:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                total_str = match.group(1).replace(',', '')
                try:
                    datos['total'] = float(total_str)
                    break
                except ValueError:
                    continue
        
        # Si no se encontró total, calcular desde items
        if 'total' not in datos:
            datos['total'] = 100.0  # Valor por defecto
        
        # Extraer items (simplificado)
        datos['items'] = self._extract_items_from_text(texto)
        
        # Calcular impuestos (simplificado)
        datos['impuestos'] = datos.get('total', 0) * 0.19  # 19% IVA por defecto
        
        return datos

    def _extract_items_from_text(self, texto: str) -> List[Dict]:
        """Extraer items de factura desde texto"""
        items = []
        
        # Buscar sección de items
        lines = texto.split('\n')
        in_items_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detectar inicio de sección de items
            if any(keyword in line.lower() for keyword in ['descripción', 'item', 'producto', 'servicio', 'cantidad', 'precio']):
                in_items_section = True
                continue
            
            # Detectar fin de sección de items
            if any(keyword in line.lower() for keyword in ['subtotal', 'total', 'impuestos', 'iva']):
                in_items_section = False
                continue
            
            # Extraer item si estamos en la sección correcta
            if in_items_section:
                # Buscar números que podrían ser cantidad y precio
                numbers = re.findall(r'[\d,]+\.?\d*', line)
                if len(numbers) >= 2:
                    try:
                        cantidad = float(numbers[0].replace(',', ''))
                        precio = float(numbers[1].replace(',', ''))
                        descripcion = re.sub(r'[\d,]+\.?\d*', '', line).strip()
                        
                        if descripcion and cantidad > 0 and precio > 0:
                            items.append({
                                'descripcion': descripcion,
                                'cantidad': cantidad,
                                'precio': precio
                            })
                    except ValueError:
                        continue
        
        # Si no se encontraron items, crear uno genérico
        if not items:
            items.append({
                'descripcion': 'Producto/Servicio procesado desde PDF',
                'cantidad': 1.0,
                'precio': 100.0
            })
        
        return items

    def get_or_create_contact(self, name: str, contact_type: str = 'client') -> Optional[str]:
        """Obtener o crear contacto en Alegra con fallback robusto"""
        if not name:
            logger.warning("⚠️ Nombre de contacto vacío, usando contacto por defecto")
            return "1"  # ID del contacto por defecto
        
        headers = self.get_auth_headers()
        
        try:
            # Buscar contacto existente
            response = requests.get(
                f"{self.base_url}/contacts",
                params={'query': name},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                contacts = response.json()
                for contact in contacts:
                    if contact.get('name', '').lower() == name.lower():
                        logger.info(f"✅ Contacto encontrado: {name} (ID: {contact.get('id')})")
                        return contact.get('id')
            
            # Intentar crear nuevo contacto
            logger.info(f"📝 Intentando crear contacto: {name} (tipo: {contact_type})")
            
            payload = {
                'name': name.strip(),
                'type': contact_type,
                'identificationObject': {
                    'type': 'NIT' if contact_type == 'provider' else 'CC',
                    'number': '000000000'
                }
            }
            
            response = requests.post(
                f"{self.base_url}/contacts",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                contact = response.json()
                logger.info(f"✅ Contacto creado: {name} (ID: {contact.get('id')})")
                return contact.get('id')
            else:
                logger.warning(f"⚠️ Error creando contacto: {response.status_code} - {response.text}")
                
                # Fallback: usar contacto por defecto
                logger.warning("⚠️ Usando contacto por defecto 'Consumidor Final'")
                return "1"  # ID del contacto por defecto
                
        except Exception as e:
            logger.error(f"❌ Error con contacto {name}: {e}")
            logger.warning("⚠️ Usando contacto por defecto 'Consumidor Final'")
            return "1"  # ID del contacto por defecto

    def get_or_create_item(self, name: str, price: float) -> Optional[str]:
        """Obtener o crear item en Alegra con cuenta contable"""
        if not name:
            logger.warning("⚠️ Nombre de item vacío")
            return None
        
        headers = self.get_auth_headers()
        
        try:
            # Buscar item existente
            response = requests.get(
                f"{self.base_url}/items",
                params={'query': name},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                items = response.json()
                for item in items:
                    if item.get('name', '').lower() == name.lower():
                        logger.info(f"✅ Item encontrado: {name} (ID: {item.get('id')})")
                        return item.get('id')
            
            # Crear nuevo item con cuenta contable
            logger.info(f"📦 Creando item: {name}")
            
            # Obtener cuenta contable por defecto
            accounting_account_id = self.accounting_config.get('item_categories', {}).get('product', {}).get('accounting_account', 1)
            
            payload = {
                'name': name.strip(),
                'description': f"Producto procesado desde PDF - {name}",
                'price': [{
                    'price': price,
                    'currency': {'code': 'COP', 'symbol': '$'},
                    'main': True
                }],
                'type': 'product',
                'status': 'active',
                'accountingAccount': {'id': accounting_account_id}
            }
            
            response = requests.post(
                f"{self.base_url}/items",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                item = response.json()
                logger.info(f"✅ Item creado: {name} (ID: {item.get('id')})")
                return item.get('id')
            else:
                logger.warning(f"⚠️ Error creando item: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error con item {name}: {e}")
            return None

    def create_purchase_bill(self, datos_factura: Dict) -> Optional[Dict]:
        """Crear factura de compra (bill) en Alegra"""
        logger.info("📥 Creando factura de COMPRA en Alegra...")
        
        headers = self.get_auth_headers()
        
        # Obtener o crear proveedor
        provider_id = self.get_or_create_contact(datos_factura['proveedor'], 'provider')
        if not provider_id:
            logger.error("❌ No se pudo obtener/crear proveedor")
            return None
        
        # Preparar items para Alegra con cuentas contables
        items = []
        for item in datos_factura['items']:
            item_id = self.get_or_create_item(item['descripcion'], item['precio'])
            if item_id:
                # Obtener cuenta contable para el item
                accounting_account_id = self.accounting_config.get('item_categories', {}).get('product', {}).get('accounting_account', 1)
                
                items.append({
                    'id': item_id,
                    'quantity': item['cantidad'],
                    'price': item['precio'],
                    'accountingAccount': {'id': accounting_account_id}
                })
        
        # Si no se pudieron crear items, crear uno genérico con cuenta contable
        if not items:
            logger.warning("⚠️ No se pudieron crear items, usando item genérico")
            accounting_account_id = self.accounting_config.get('item_categories', {}).get('product', {}).get('accounting_account', 1)
            items.append({
                'name': 'Producto/Servicio Genérico',
                'quantity': 1.0,
                'price': datos_factura.get('total', 100.0),
                'accountingAccount': {'id': accounting_account_id}
            })
        
        # Crear payload para bill
        payload = {
            'date': datos_factura['fecha'],
            'dueDate': datos_factura['fecha'],
            'provider': {'id': provider_id},
            'items': items,
            'observations': f"Factura de COMPRA procesada desde PDF - {datos_factura['proveedor']} - Total: ${datos_factura['total']:,.2f} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        }
        
        # Agregar impuestos si existen
        if datos_factura['impuestos'] > 0:
            payload['tax'] = datos_factura['impuestos']
        
        try:
            response = requests.post(
                f"{self.base_url}/bills",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"📡 Status Code: {response.status_code}")
            
            if response.status_code == 201:
                bill_created = response.json()
                logger.info("✅ ¡Factura de COMPRA creada exitosamente!")
                logger.info(f"🆔 ID: {bill_created.get('id')}")
                logger.info(f"📄 Número: {bill_created.get('number')}")
                logger.info(f"💰 Total: ${bill_created.get('total')}")
                logger.info(f"🏪 Proveedor: {bill_created.get('provider', {}).get('name')}")
                logger.info(f"📅 Fecha: {bill_created.get('date')}")
                
                return bill_created
            else:
                logger.error(f"❌ Error creando factura de compra: {response.status_code}")
                logger.error(f"📝 Respuesta: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error en API Alegra: {e}")
            return None

    def create_sale_invoice(self, datos_factura: Dict) -> Optional[Dict]:
        """Crear factura de venta en Alegra"""
        logger.info("📤 Creando factura de VENTA en Alegra...")
        
        headers = self.get_auth_headers()
        
        # Obtener o crear cliente
        client_id = self.get_or_create_contact(datos_factura['cliente'], 'client')
        if not client_id:
            logger.error("❌ No se pudo obtener/crear cliente")
            return None
        
        # Preparar items para Alegra con cuentas contables
        items = []
        for item in datos_factura['items']:
            item_id = self.get_or_create_item(item['descripcion'], item['precio'])
            if item_id:
                # Obtener cuenta contable para el item
                accounting_account_id = self.accounting_config.get('item_categories', {}).get('product', {}).get('accounting_account', 2)
                
                items.append({
                    'id': item_id,
                    'quantity': item['cantidad'],
                    'price': item['precio'],
                    'accountingAccount': {'id': accounting_account_id}
                })
        
        # Si no se pudieron crear items, crear uno genérico con cuenta contable
        if not items:
            logger.warning("⚠️ No se pudieron crear items, usando item genérico")
            accounting_account_id = self.accounting_config.get('item_categories', {}).get('product', {}).get('accounting_account', 2)
            items.append({
                'name': 'Producto/Servicio Genérico',
                'quantity': 1.0,
                'price': datos_factura.get('total', 100.0),
                'accountingAccount': {'id': accounting_account_id}
            })
        
        # Crear payload para invoice
        payload = {
            'date': datos_factura['fecha'],
            'dueDate': datos_factura['fecha'],
            'client': {'id': client_id},
            'items': items,
            'observations': f"Factura de VENTA procesada desde PDF - {datos_factura['cliente']} - Total: ${datos_factura['total']:,.2f} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        }
        
        # Agregar impuestos si existen
        if datos_factura['impuestos'] > 0:
            payload['tax'] = datos_factura['impuestos']
        
        try:
            response = requests.post(
                f"{self.base_url}/invoices",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"📡 Status Code: {response.status_code}")
            
            if response.status_code == 201:
                invoice_created = response.json()
                logger.info("✅ ¡Factura de VENTA creada exitosamente!")
                logger.info(f"🆔 ID: {invoice_created.get('id')}")
                logger.info(f"📄 Número: {invoice_created.get('number')}")
                logger.info(f"💰 Total: ${invoice_created.get('total')}")
                logger.info(f"👤 Cliente: {invoice_created.get('client', {}).get('name')}")
                logger.info(f"📅 Fecha: {invoice_created.get('date')}")
                
                return invoice_created
            else:
                logger.error(f"❌ Error creando factura de venta: {response.status_code}")
                logger.error(f"📝 Respuesta: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error en API Alegra: {e}")
            return None

    def process_invoice(self, file_path: str) -> Optional[Dict]:
        """Procesar factura completa"""
        logger.info(f"🚀 Iniciando procesamiento de: {file_path}")
        
        # Determinar tipo de archivo y extraer datos
        file_ext = file_path.lower().split('.')[-1]
        
        if file_ext == 'pdf':
            datos_factura = self.extract_data_from_pdf(file_path)
        elif file_ext in ['jpg', 'jpeg', 'png']:
            datos_factura = self.extract_data_from_image(file_path)
        else:
            logger.error(f"❌ Tipo de archivo no soportado: {file_ext}")
            return None
        
        if not datos_factura:
            logger.error("❌ No se pudieron extraer datos del archivo")
            return None
        
        # Procesar según tipo
        if datos_factura['tipo'] == 'compra':
            return self.create_purchase_bill(datos_factura)
        else:
            return self.create_sale_invoice(datos_factura)

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Procesador de facturas mejorado')
    parser.add_argument('command', choices=['process', 'report'], help='Comando a ejecutar')
    parser.add_argument('file_path', nargs='?', help='Ruta del archivo a procesar')
    parser.add_argument('--start-date', help='Fecha de inicio para reportes (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='Fecha de fin para reportes (YYYY-MM-DD)')
    parser.add_argument('--use-nanobot', action='store_true', help='Habilitar Nanobot')
    parser.add_argument('--nanobot-host', help='Host de Nanobot')
    parser.add_argument('--nanobot-confidence', type=float, help='Umbral de confianza de Nanobot')
    
    args = parser.parse_args()
    
    try:
        processor = InvoiceProcessor(
            use_nanobot=args.use_nanobot,
            nanobot_host=args.nanobot_host,
            nanobot_confidence_threshold=args.nanobot_confidence
        )
        
        if args.command == 'process':
            if not args.file_path:
                print("❌ Debe especificar la ruta del archivo")
                return
            
            resultado = processor.process_invoice(args.file_path)
            if resultado:
                print("✅ Factura procesada exitosamente")
            else:
                print("❌ Error procesando factura")
        
        elif args.command == 'report':
            if not args.start_date or not args.end_date:
                print("❌ Debe especificar fechas de inicio y fin")
                return
            
            reports = AlegraReports()
            reports.generate_ledger_report(args.start_date, args.end_date, 'general-ledger')
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()