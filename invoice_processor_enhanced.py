#!/usr/bin/env python3
"""
Sistema mejorado de procesamiento de facturas - Detección automática y parsing robusto
Evolución de InvoiceBot a bot contable completo con integración Alegra
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
            datos = self._parse_invoice_data(texto, invoice_type)
            
            if datos:
                logger.info("📊 Datos extraídos exitosamente:")
                logger.info(f"   📅 Fecha: {datos['fecha']}")
                logger.info(f"   🏪 {'Proveedor' if invoice_type == 'compra' else 'Cliente'}: {datos['proveedor']}")
                logger.info(f"   📦 Productos: {len(datos['items'])}")
                logger.info(f"   💰 Total: ${datos['total']:,.2f}")
            
            return datos
            
        except Exception as e:
            logger.error(f"❌ Error procesando PDF: {e}")
            return None
    
    def extract_data_from_image(self, image_path: str) -> Optional[Dict]:
        """
        Extraer datos de imagen (JPG/PNG) usando OCR
        """
        if not OCR_AVAILABLE:
            logger.error("❌ OCR libraries not available. Install pytesseract, Pillow, and opencv-python")
            return None
            
        logger.info(f"🖼️ Procesando imagen: {image_path}")
        
        try:
            # Cargar imagen
            if Image is None:
                logger.error("OCR no disponible, falta Pillow")
                return None

            image = Image.open(image_path)
            
            # Preprocesar imagen para mejorar OCR
            processed_image = self._preprocess_image_for_ocr(image)
            
            # Extraer texto usando OCR
            texto = pytesseract.image_to_string(processed_image, lang='spa+eng')
            
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
            datos = self._parse_invoice_data(texto, invoice_type)
            
            if datos:
                logger.info("📊 Datos extraídos exitosamente:")
                logger.info(f"   📅 Fecha: {datos['fecha']}")
                logger.info(f"   🏪 {'Proveedor' if invoice_type == 'compra' else 'Cliente'}: {datos['proveedor']}")
                logger.info(f"   📦 Productos: {len(datos['items'])}")
                logger.info(f"   💰 Total: ${datos['total']:,.2f}")
            
            return datos
            
        except Exception as e:
            logger.error(f"❌ Error procesando imagen {image_path}: {e}")
            return None
    
    def _preprocess_image_for_ocr(self, image):
        """
        Preprocesar imagen para mejorar la precisión del OCR
        """
        try:
            # Convertir a escala de grises
            if image.mode != 'L':
                image = image.convert('L')
            
            # Convertir PIL a OpenCV (asegurar que sea escala de grises)
            if image.mode == 'L':
                cv_image = np.array(image)
            else:
                cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Aplicar filtros para mejorar OCR
            # Reducir ruido
            cv_image = cv2.medianBlur(cv_image, 3)
            
            # Aplicar umbralización adaptativa
            cv_image = cv2.adaptiveThreshold(
                cv_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Convertir de vuelta a PIL
            processed_image = Image.fromarray(cv_image) if Image is not None else image
            
            return processed_image
            
        except Exception as e:
            logger.warning(f"⚠️ Error en preprocesamiento de imagen: {e}")
            return image
    
    def _parse_invoice_data(self, texto: str, invoice_type: str) -> Dict:
        """Parsear datos de la factura con patrones mejorados"""
        
        # Extraer fecha con múltiples patrones
        fecha = self._extract_date(texto)
        
        # Extraer vendedor/proveedor
        vendedor = self._extract_vendor(texto, invoice_type)
        
        # Extraer items con parsing mejorado
        items = self._extract_items(texto)
        
        # Extraer totales con múltiples patrones
        subtotal, impuestos, total = self._extract_totals(texto)
        
        datos = {
            'tipo': invoice_type,
            'fecha': fecha,
            'proveedor': vendedor,
            'cliente': 'Cliente desde PDF' if invoice_type == 'venta' else vendedor,
            'items': items,
            'subtotal': subtotal,
            'impuestos': impuestos,
            'total': total
        }
        
        return datos
    
    def _extract_date(self, texto: str) -> str:
        """Extraer fecha con múltiples patrones"""
        date_patterns = [
            r'Fecha:\s*(\d{1,2}-\d{1,2}-\d{4})',
            r'Date:\s*(\d{1,2}-\d{1,2}-\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{1,2}-\d{1,2})',
            r'(\d{1,2}-\d{1,2}-\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, texto)
            if match:
                fecha = match.group(1)
                # Normalizar formato
                if '-' in fecha and len(fecha.split('-')[0]) == 2:
                    # Formato DD-MM-YYYY
                    parts = fecha.split('-')
                    if len(parts) == 3:
                        day, month, year = parts
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                elif '/' in fecha:
                    # Formato DD/MM/YYYY
                    parts = fecha.split('/')
                    if len(parts) == 3:
                        day, month, year = parts
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                else:
                    return fecha
        
        # Si no se encuentra fecha, usar fecha actual
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_vendor(self, texto: str, invoice_type: str) -> str:
        """Extraer vendedor/proveedor con múltiples patrones"""
        patterns = [
            r'Factura electrónica de venta #\d+\n([^\n]+)',
            r'Proveedor:\s*([^\n]+)',
            r'Vendor:\s*([^\n]+)',
            r'Cliente:\s*([^\n]+)',
            r'Customer:\s*([^\n]+)',
            r'From:\s*([^\n]+)',
            r'Bill To:\s*([^\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                vendor = match.group(1).strip()
                if vendor and len(vendor) > 2:
                    return vendor
        
        return "Proveedor Desconocido" if invoice_type == 'compra' else "Cliente Desconocido"
    
    def _extract_items(self, texto: str) -> List[Dict]:
        """Extraer items con parsing mejorado"""
        items = []
        
        # Patrón para extraer productos con código y descripción
        item_pattern = r'(\d+)\s*-\s*(.+?)\s*(?:Impuestos|Total|Subtotal|$)'
        matches = re.findall(item_pattern, texto, re.DOTALL)
        
        for match in matches:
            codigo = match[0]
            descripcion = match[1].strip()
            
            # Buscar cantidad y precio para este item
            qty_match = re.search(rf'{codigo}.*?(\d+)\s+Unidad', texto)
            cantidad = float(qty_match.group(1)) if qty_match else 1.0
            
            price_match = re.search(rf'{codigo}.*?Precio unit\.\s*\$?([\d,]+\.?\d*)', texto)
            precio = float(price_match.group(1).replace(',', '')) if price_match else 0.0
            
            items.append({
                'codigo': codigo,
                'descripcion': f"{codigo} - {descripcion}",
                'cantidad': cantidad,
                'precio': precio
            })
        
        # Si no se encontraron items, crear uno genérico
        if not items:
            items.append({
                'codigo': '001',
                'descripcion': 'Producto no identificado',
                'cantidad': 1.0,
                'precio': 0.0
            })
        
        return items
    
    def _extract_totals(self, texto: str) -> Tuple[float, float, float]:
        """Extraer totales con múltiples patrones"""
        # Patrones para subtotal
        subtotal_patterns = [
            r'Subtotal\s+\$?([\d,]+\.?\d*)',
            r'Sub Total\s+\$?([\d,]+\.?\d*)',
            r'Sub-total\s+\$?([\d,]+\.?\d*)'
        ]
        
        subtotal = 0.0
        for pattern in subtotal_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                subtotal = float(match.group(1).replace(',', ''))
                break
        
        # Patrones para impuestos
        tax_patterns = [
            r'Impuestos\s+\$?([\d,]+\.?\d*)',
            r'IVA\s+\$?([\d,]+\.?\d*)',
            r'Tax\s+\$?([\d,]+\.?\d*)',
            r'Taxes\s+\$?([\d,]+\.?\d*)'
        ]
        
        impuestos = 0.0
        for pattern in tax_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                impuestos = float(match.group(1).replace(',', ''))
                break
        
        # Patrones para total
        total_patterns = [
            r'Total[:\s]+\d+\s+Unidad\s+\$?([\d,]+\.?\d*)',
            r'Total[:\s]+\$?([\d,]+\.?\d*)',
            r'Grand Total\s+\$?([\d,]+\.?\d*)',
            r'Amount Due\s+\$?([\d,]+\.?\d*)'
        ]
        
        total = 0.0
        for pattern in total_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                total = float(match.group(1).replace(',', ''))
                break
        
        # Si no se encontró subtotal pero sí total, calcularlo
        if subtotal == 0.0 and total > 0:
            subtotal = total - impuestos
        
        return subtotal, impuestos, total
    
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
        """Obtener o crear item en Alegra"""
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
            
            # Crear nuevo item si no existe
            payload = {
                'name': name,
                'price': price,
                'description': f"Item creado automáticamente - {name}"
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
                logger.error(f"❌ Error creando item: {response.status_code} - {response.text}")
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
        
        # Preparar items para Alegra
        items = []
        for item in datos_factura['items']:
            item_id = self.get_or_create_item(item['descripcion'], item['precio'])
            if item_id:
                items.append({
                    'id': item_id,
                    'quantity': item['cantidad'],
                    'price': item['precio']
                })
        
        if not items:
            logger.error("❌ No se pudieron crear items")
            return None
        
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
        
        # Preparar items para Alegra
        items = []
        for item in datos_factura['items']:
            item_id = self.get_or_create_item(item['descripcion'], item['precio'])
            if item_id:
                items.append({
                    'id': item_id,
                    'quantity': item['cantidad'],
                    'price': item['precio']
                })
        
        if not items:
            logger.error("❌ No se pudieron crear items")
            return None
        
        # Calcular fecha de vencimiento
        fecha_vencimiento = datetime.strptime(datos_factura['fecha'], '%Y-%m-%d') + timedelta(days=30)
        
        # Crear payload para invoice
        payload = {
            'date': datos_factura['fecha'],
            'dueDate': fecha_vencimiento.strftime('%Y-%m-%d'),
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
                logger.info(f"📅 Vencimiento: {invoice_created.get('dueDate')}")
                
                return invoice_created
            else:
                logger.error(f"❌ Error creando factura de venta: {response.status_code}")
                logger.error(f"📝 Respuesta: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error en API Alegra: {e}")
            return None
    
    def register_local_purchase(self, datos_factura: Dict) -> bool:
        """Registrar factura de compra localmente (backup)"""
        logger.info("📥 Registrando factura de COMPRA localmente...")
        
        try:
            # Crear archivo de registro
            registro_file = f"facturas_compra_{datetime.now().strftime('%Y%m%d')}.txt"
            
            registro_entry = f"""
FACTURA DE COMPRA REGISTRADA
============================
Fecha: {datos_factura['fecha']}
Proveedor: {datos_factura['proveedor']}
Items: {len(datos_factura['items'])}
Subtotal: ${datos_factura['subtotal']:,.2f}
Impuestos: ${datos_factura['impuestos']:,.2f}
Total: ${datos_factura['total']:,.2f}
Registrado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
============================
"""
            
            with open(registro_file, 'a', encoding='utf-8') as f:
                f.write(registro_entry)
            
            # También crear registro JSON
            json_file = f"facturas_compra_{datetime.now().strftime('%Y%m%d')}.json"
            
            registro_json = {
                "tipo": "compra",
                "fecha": datos_factura['fecha'],
                "proveedor": datos_factura['proveedor'],
                "items": datos_factura['items'],
                "subtotal": datos_factura['subtotal'],
                "impuestos": datos_factura['impuestos'],
                "total": datos_factura['total'],
                "registrado": datetime.now().isoformat()
            }
            
            # Cargar registros existentes o crear lista vacía
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    registros = json.load(f)
            except FileNotFoundError:
                registros = []
            
            registros.append(registro_json)
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(registros, f, indent=2, ensure_ascii=False)
            
            logger.info("✅ Factura de compra registrada localmente!")
            logger.info(f"📁 Archivos: {registro_file}, {json_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error registrando factura local: {e}")
            return False

    def process_invoice_file(self, file_path: str) -> Optional[Dict]:
        """
        Procesar archivo de factura (PDF o imagen) de forma unificada
        """
        logger.info(f"🔄 Procesando archivo: {file_path}")
        
        # Determinar tipo de archivo
        file_ext = file_path.lower().split('.')[-1]
        
        if file_ext == 'pdf':
            return self.extract_data_from_pdf(file_path)
        elif file_ext in ['jpg', 'jpeg', 'png']:
            return self.extract_data_from_image(file_path)
        else:
            logger.error(f"❌ Tipo de archivo no soportado: {file_ext}")
            return None

def main():
    """Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='InvoiceBot - Sistema de procesamiento de facturas')
    parser.add_argument('command', choices=['process', 'report'], help='Comando a ejecutar')
    parser.add_argument('pdf_path', nargs='?', help='Ruta al archivo (PDF, JPG, PNG)')
    parser.add_argument('--start-date', help='Fecha de inicio para reportes (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='Fecha de fin para reportes (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    if args.command == 'process':
        if not args.pdf_path:
            print("❌ Se requiere ruta al archivo para procesar")
            return
        
        if not os.path.exists(args.pdf_path):
            print(f"❌ Archivo no encontrado: {args.pdf_path}")
            return
        
        # Verificar tipo de archivo soportado
        file_ext = args.pdf_path.lower().split('.')[-1]
        if file_ext not in ['pdf', 'jpg', 'jpeg', 'png']:
            print(f"❌ Tipo de archivo no soportado: {file_ext}")
            print("✅ Tipos soportados: PDF, JPG, JPEG, PNG")
            return
        
        # Procesar factura (PDF o imagen)
        processor = InvoiceProcessor()
        datos = processor.process_invoice_file(args.pdf_path)
        
        if not datos:
            print("❌ No se pudieron extraer datos del PDF")
            return
        
        # Procesar según el tipo detectado
        if datos['tipo'] == 'compra':
            # Crear bill en Alegra
            resultado = processor.create_purchase_bill(datos)
            if resultado:
                # También registrar localmente como backup
                processor.register_local_purchase(datos)
                print("\n🎉 ¡Factura de COMPRA procesada exitosamente!")
                print("✅ Se creó en Alegra (bill)")
                print("✅ Se registró localmente como backup")
            else:
                print("\n⚠️ Error procesando factura de compra")
        else:  # venta
            resultado = processor.create_sale_invoice(datos)
            if resultado:
                print("\n🎉 ¡Factura de VENTA procesada exitosamente!")
                print("✅ Se creó en Alegra (invoice)")
            else:
                print("\n⚠️ Error procesando factura de venta")
    
    elif args.command == 'report':
        if not args.start_date or not args.end_date:
            print("❌ Se requieren --start-date y --end-date para reportes")
            return
        
        # Generar reportes
        reporter = AlegraReports()
        
        # Generar reporte de ledger general
        print("📊 Generando reporte de ledger general...")
        general_ledger = reporter.generate_ledger_report(
            args.start_date, 
            args.end_date, 
            'general-ledger'
        )
        
        # Generar balance de prueba
        print("📊 Generando balance de prueba...")
        trial_balance = reporter.generate_ledger_report(
            args.start_date, 
            args.end_date, 
            'trial-balance'
        )
        
        # Generar diario
        print("📊 Generando diario...")
        journal = reporter.generate_ledger_report(
            args.start_date, 
            args.end_date, 
            'journal'
        )
        
        if general_ledger and trial_balance and journal:
            print("\n🎉 ¡Todos los reportes generados exitosamente!")
            print("✅ Reportes guardados en carpeta 'reports/'")
        else:
            print("\n⚠️ Algunos reportes no se pudieron generar")

if __name__ == "__main__":
    main()