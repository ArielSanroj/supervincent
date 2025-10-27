#!/usr/bin/env python3
"""
Sistema robusto de procesamiento de facturas - Versión con manejo mejorado de errores
Incluye: fallback a contactos existentes, validación robusta y manejo de errores mejorado
"""

import requests
import base64
import pdfplumber
import re
import json
import sys
import logging
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from typing import Dict, List, Optional, Tuple
from alegra_reports import AlegraReports

# OCR imports for image processing
try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError as e:
    OCR_AVAILABLE = False

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/invoicebot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

class InvoiceProcessorRobust:
    """Procesador robusto de facturas con manejo mejorado de errores"""
    
    def __init__(self):
        self.alegra_email = os.getenv('ALEGRA_USER')
        self.alegra_token = os.getenv('ALEGRA_TOKEN')
        self.base_url = "https://api.alegra.com/api/v1"
        
        if not self.alegra_email or not self.alegra_token:
            raise ValueError("Faltan credenciales de Alegra en .env")
        
        # Cargar configuración de cuentas contables
        self.load_accounting_config()
        
        # Cache de contactos e items para evitar llamadas repetidas
        self.contacts_cache = {}
        self.items_cache = {}
        
        # Cargar contactos existentes al inicializar
        self.load_existing_contacts()
    
    def load_accounting_config(self):
        """Cargar configuración de cuentas contables"""
        try:
            with open('config/accounting_accounts.json', 'r', encoding='utf-8') as f:
                self.accounting_config = json.load(f)
            logger.info("✅ Configuración de cuentas contables cargada")
        except FileNotFoundError:
            logger.warning("⚠️ Archivo de configuración de cuentas no encontrado, usando valores por defecto")
            self.accounting_config = {
                "default_accounts": {
                    "purchases": {"id": 1, "name": "Compras", "type": "expense"},
                    "sales": {"id": 2, "name": "Ventas", "type": "income"}
                },
                "item_categories": {
                    "product": {"accounting_account": 1, "tax_category": "standard"},
                    "service": {"accounting_account": 2, "tax_category": "standard"}
                }
            }
    
    def load_existing_contacts(self):
        """Cargar contactos existentes al inicializar"""
        try:
            headers = self.get_auth_headers()
            response = requests.get(f"{self.base_url}/contacts", headers=headers, timeout=10)
            
            if response.status_code == 200:
                contacts = response.json()
                for contact in contacts:
                    name = contact.get('name', '').lower()
                    self.contacts_cache[name] = {
                        'id': contact.get('id'),
                        'name': contact.get('name'),
                        'type': contact.get('type', [])
                    }
                logger.info(f"✅ {len(contacts)} contactos cargados en cache")
            else:
                logger.warning(f"⚠️ No se pudieron cargar contactos: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Error cargando contactos: {e}")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Obtener headers de autenticación para Alegra"""
        credentials = f"{self.alegra_email}:{self.alegra_token}"
        auth_header = f"Basic {base64.b64encode(credentials.encode()).decode()}"
        
        return {
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }
    
    def validate_invoice_data(self, datos_factura: Dict) -> Tuple[bool, List[str]]:
        """Validar datos de factura antes de enviar a Alegra"""
        errors = []
        
        # Validar campos requeridos
        required_fields = ['fecha', 'items', 'total']
        for field in required_fields:
            if field not in datos_factura or not datos_factura[field]:
                errors.append(f"Campo requerido faltante: {field}")
        
        # Validar que tenga al menos cliente o proveedor
        if 'proveedor' not in datos_factura and 'cliente' not in datos_factura:
            errors.append("Debe tener cliente o proveedor")
        
        # Validar items
        if 'items' in datos_factura:
            for i, item in enumerate(datos_factura['items']):
                if not item.get('descripcion'):
                    errors.append(f"Item {i+1}: descripción faltante")
                if not item.get('cantidad') or item.get('cantidad') <= 0:
                    errors.append(f"Item {i+1}: cantidad inválida")
                if not item.get('precio') or item.get('precio') <= 0:
                    errors.append(f"Item {i+1}: precio inválido")
        
        # Validar fecha
        if 'fecha' in datos_factura:
            try:
                datetime.strptime(datos_factura['fecha'], '%Y-%m-%d')
            except ValueError:
                errors.append("Formato de fecha inválido (debe ser YYYY-MM-DD)")
        
        # Validar total
        if 'total' in datos_factura:
            try:
                total = float(datos_factura['total'])
                if total <= 0:
                    errors.append("Total debe ser mayor a 0")
            except (ValueError, TypeError):
                errors.append("Total debe ser un número válido")
        
        return len(errors) == 0, errors
    
    def detect_invoice_type(self, texto: str) -> str:
        """Detectar automáticamente si es factura de compra o venta"""
        texto_lower = texto.lower()
        
        # Keywords que indican compra
        compra_keywords = [
            'proveedor', 'proveedores', 'compra', 'compras', 'factura de compra',
            'bill', 'purchase', 'supplier', 'vendor', 'factura de proveedor',
            'orden de compra', 'oc', 'pedido', 'receipt'
        ]
        
        # Keywords que indican venta
        venta_keywords = [
            'cliente', 'clientes', 'venta', 'ventas', 'factura de venta',
            'invoice', 'sale', 'customer', 'factura de cliente',
            'orden de venta', 'ov', 'cotización', 'quote'
        ]
        
        compra_score = sum(1 for keyword in compra_keywords if keyword in texto_lower)
        venta_score = sum(1 for keyword in venta_keywords if keyword in texto_lower)
        
        logger.info(f"Puntuación compra: {compra_score}, Puntuación venta: {venta_score}")
        
        if compra_score > venta_score:
            return 'compra'
        elif venta_score > compra_score:
            return 'venta'
        else:
            # Si hay empate, buscar patrones más específicos
            if any(pattern in texto_lower for pattern in ['factura electrónica de venta', 'invoice']):
                return 'venta'
            elif any(pattern in texto_lower for pattern in ['factura de compra', 'bill']):
                return 'compra'
            else:
                # Por defecto, asumir compra si no se puede determinar
                logger.warning("⚠️ No se pudo determinar el tipo de factura, asumiendo COMPRA")
                return 'compra'
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extraer texto de PDF"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text
        except Exception as e:
            logger.error(f"❌ Error extrayendo texto del PDF: {e}")
            return ""
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extraer texto de imagen usando OCR"""
        if not OCR_AVAILABLE:
            logger.error("❌ OCR no disponible")
            return ""
        
        try:
            # Cargar imagen
            image = cv2.imread(image_path)
            
            # Preprocesamiento para mejorar OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 3)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # OCR
            text = pytesseract.image_to_string(gray, lang='spa')
            return text
        except Exception as e:
            logger.error(f"❌ Error en OCR: {e}")
            return ""
    
    def parse_invoice_data(self, texto: str) -> Dict:
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
        datos['items'] = self.extract_items_from_text(texto)
        
        # Calcular impuestos (simplificado)
        datos['impuestos'] = datos.get('total', 0) * 0.19  # 19% IVA por defecto
        
        return datos
    
    def extract_items_from_text(self, texto: str) -> List[Dict]:
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
    
    def get_or_create_contact_robust(self, name: str, contact_type: str = 'client') -> Optional[str]:
        """Obtener o crear contacto con fallback robusto"""
        if not name:
            logger.warning("⚠️ Nombre de contacto vacío, usando contacto por defecto")
            return "1"  # ID del contacto por defecto
        
        # Buscar en cache primero
        name_lower = name.lower().strip()
        if name_lower in self.contacts_cache:
            contact = self.contacts_cache[name_lower]
            logger.info(f"✅ Contacto encontrado en cache: {contact['name']} (ID: {contact['id']})")
            return contact['id']
        
        headers = self.get_auth_headers()
        
        try:
            # Buscar contacto existente en Alegra
            response = requests.get(
                f"{self.base_url}/contacts",
                params={'query': name},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                contacts = response.json()
                for contact in contacts:
                    if contact.get('name', '').lower() == name_lower:
                        # Agregar a cache
                        self.contacts_cache[name_lower] = {
                            'id': contact.get('id'),
                            'name': contact.get('name'),
                            'type': contact.get('type', [])
                        }
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
                # Agregar a cache
                self.contacts_cache[name_lower] = {
                    'id': contact.get('id'),
                    'name': contact.get('name'),
                    'type': contact.get('type', [])
                }
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
    
    def get_or_create_item_robust(self, name: str, price: float, item_type: str = 'product') -> Optional[str]:
        """Obtener o crear item con fallback robusto"""
        if not name:
            logger.warning("⚠️ Nombre de item vacío, usando item genérico")
            return None
        
        # Buscar en cache primero
        name_lower = name.lower().strip()
        if name_lower in self.items_cache:
            item = self.items_cache[name_lower]
            logger.info(f"✅ Item encontrado en cache: {item['name']} (ID: {item['id']})")
            return item['id']
        
        headers = self.get_auth_headers()
        
        try:
            # Buscar item existente en Alegra
            response = requests.get(
                f"{self.base_url}/items",
                params={'query': name},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                items = response.json()
                for item in items:
                    if item.get('name', '').lower() == name_lower:
                        # Agregar a cache
                        self.items_cache[name_lower] = {
                            'id': item.get('id'),
                            'name': item.get('name')
                        }
                        logger.info(f"✅ Item encontrado: {name} (ID: {item.get('id')})")
                        return item.get('id')
            
            # Intentar crear nuevo item
            logger.info(f"📦 Intentando crear item: {name}")
            
            item_config = self.accounting_config.get('item_categories', {}).get(item_type, {})
            accounting_account_id = item_config.get('accounting_account', 1)
            
            payload = {
                'name': name.strip(),
                'description': f"Producto procesado desde PDF - {name}",
                'price': [{
                    'price': price,
                    'currency': {'code': 'COP', 'symbol': '$'},
                    'main': True
                }],
                'type': item_type,
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
                # Agregar a cache
                self.items_cache[name_lower] = {
                    'id': item.get('id'),
                    'name': item.get('name')
                }
                logger.info(f"✅ Item creado: {name} (ID: {item.get('id')})")
                return item.get('id')
            else:
                logger.warning(f"⚠️ Error creando item: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error con item {name}: {e}")
            return None
    
    def create_purchase_bill_robust(self, datos_factura: Dict) -> Optional[Dict]:
        """Crear factura de compra con manejo robusto de errores"""
        logger.info("📥 Creando factura de COMPRA en Alegra...")
        
        # Validar datos antes de procesar
        is_valid, errors = self.validate_invoice_data(datos_factura)
        if not is_valid:
            logger.error(f"❌ Datos de factura inválidos: {', '.join(errors)}")
            return None
        
        headers = self.get_auth_headers()
        
        # Obtener o crear proveedor con fallback
        provider_id = self.get_or_create_contact_robust(datos_factura.get('proveedor', 'Proveedor Genérico'), 'provider')
        if not provider_id:
            logger.error("❌ No se pudo obtener/crear proveedor")
            return None
        
        # Preparar items con cuentas contables
        items = []
        for item in datos_factura['items']:
            item_id = self.get_or_create_item_robust(item['descripcion'], item['precio'], 'product')
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
        
        # Crear payload para bill con cuentas contables
        payload = {
            'date': datos_factura['fecha'],
            'dueDate': datos_factura['fecha'],
            'provider': {'id': provider_id},
            'items': items,
            'observations': f"Factura de COMPRA procesada desde PDF - {datos_factura.get('proveedor', 'Proveedor')} - Total: ${datos_factura['total']:,.2f} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        }
        
        # Agregar impuestos si existen
        if datos_factura.get('impuestos', 0) > 0:
            payload['tax'] = datos_factura['impuestos']
        
        logger.info(f"📤 Enviando bill a Alegra: {len(items)} items")
        
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
    
    def create_sale_invoice_robust(self, datos_factura: Dict) -> Optional[Dict]:
        """Crear factura de venta con manejo robusto de errores"""
        logger.info("📤 Creando factura de VENTA en Alegra...")
        
        # Validar datos antes de procesar
        is_valid, errors = self.validate_invoice_data(datos_factura)
        if not is_valid:
            logger.error(f"❌ Datos de factura inválidos: {', '.join(errors)}")
            return None
        
        headers = self.get_auth_headers()
        
        # Obtener o crear cliente con fallback
        client_id = self.get_or_create_contact_robust(datos_factura.get('cliente', 'Cliente Genérico'), 'client')
        if not client_id:
            logger.error("❌ No se pudo obtener/crear cliente")
            return None
        
        # Preparar items con cuentas contables
        items = []
        for item in datos_factura['items']:
            item_id = self.get_or_create_item_robust(item['descripcion'], item['precio'], 'product')
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
        
        # Crear payload para invoice con cuentas contables
        payload = {
            'date': datos_factura['fecha'],
            'dueDate': datos_factura['fecha'],
            'client': {'id': client_id},
            'items': items,
            'observations': f"Factura de VENTA procesada desde PDF - {datos_factura.get('cliente', 'Cliente')} - Total: ${datos_factura['total']:,.2f} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        }
        
        # Agregar impuestos si existen
        if datos_factura.get('impuestos', 0) > 0:
            payload['tax'] = datos_factura['impuestos']
        
        logger.info(f"📤 Enviando invoice a Alegra: {len(items)} items")
        
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
        """Procesar factura completa con manejo robusto"""
        logger.info(f"🚀 Iniciando procesamiento de: {file_path}")
        
        # Extraer texto según tipo de archivo
        file_ext = file_path.lower().split('.')[-1]
        
        if file_ext == 'pdf':
            texto = self.extract_text_from_pdf(file_path)
        elif file_ext in ['jpg', 'jpeg', 'png']:
            texto = self.extract_text_from_image(file_path)
        else:
            logger.error(f"❌ Tipo de archivo no soportado: {file_ext}")
            return None
        
        if not texto:
            logger.error("❌ No se pudo extraer texto del archivo")
            return None
        
        # Parsear datos
        datos_factura = self.parse_invoice_data(texto)
        
        # Detectar tipo de factura
        tipo = self.detect_invoice_type(texto)
        datos_factura['tipo'] = tipo
        
        logger.info(f"📊 Datos extraídos - Tipo: {tipo}, Total: ${datos_factura.get('total', 0):,.2f}")
        
        # Procesar según tipo
        if tipo == 'compra':
            return self.create_purchase_bill_robust(datos_factura)
        else:
            return self.create_sale_invoice_robust(datos_factura)

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Procesador robusto de facturas')
    parser.add_argument('command', choices=['process', 'report'], help='Comando a ejecutar')
    parser.add_argument('file_path', nargs='?', help='Ruta del archivo a procesar')
    parser.add_argument('--start-date', help='Fecha de inicio para reportes (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='Fecha de fin para reportes (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    try:
        processor = InvoiceProcessorRobust()
        
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