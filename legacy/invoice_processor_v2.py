#!/usr/bin/env python3
"""
InvoiceBot v2.0 - Bot Contable Integral
Sistema completo de procesamiento de facturas con detección automática
y integración completa con Alegra para contabilidad.
"""

import requests
import base64
import pdfplumber
import re
import json
import sys
import os
import logging
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno
load_dotenv()

class InvoiceBot:
    """Bot contable integral para procesamiento de facturas"""
    
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.setup_alegra_auth()
        
    def setup_logging(self):
        """Configurar sistema de logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/invoicebot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self):
        """Cargar configuración desde archivo JSON"""
        try:
            with open('config/settings.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.logger.warning("Archivo de configuración no encontrado, usando valores por defecto")
            self.config = {
                "parsing": {
                    "keywords_compra": ["proveedor", "compra", "bill", "invoice"],
                    "keywords_venta": ["cliente", "venta", "sale"]
                }
            }
    
    def setup_alegra_auth(self):
        """Configurar autenticación con Alegra"""
        self.alegra_email = os.getenv('ALEGRA_USER')
        self.alegra_token = os.getenv('ALEGRA_TOKEN')
        self.base_url = os.getenv('ALEGRA_BASE_URL', 'https://api.alegra.com/api/v1')
        
        if not self.alegra_email or not self.alegra_token:
            raise ValueError("ALEGRA_USER y ALEGRA_TOKEN deben estar configurados en .env")
        
        credentials = f"{self.alegra_email}:{self.alegra_token}"
        self.auth_header = f"Basic {base64.b64encode(credentials.encode()).decode()}"
        self.headers = {
            'Authorization': self.auth_header,
            'Content-Type': 'application/json'
        }
    
    def extract_data_from_pdf(self, pdf_path):
        """Extraer datos del PDF con detección automática de tipo"""
        self.logger.info(f"Procesando PDF: {pdf_path}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                texto = ''
                for page in pdf.pages:
                    texto += page.extract_text() or ''
            
            self.logger.debug(f"Texto extraído: {texto[:200]}...")
            
            # Detectar tipo automáticamente
            tipo = self.detect_invoice_type(texto)
            
            # Extraer datos básicos
            fecha = self.extract_date(texto)
            vendedor = self.extract_vendor(texto)
            producto = self.extract_product(texto)
            precios = self.extract_prices(texto)
            impuestos = self.extract_taxes(texto)
            
            datos = {
                'tipo': tipo,
                'fecha': fecha,
                'proveedor': vendedor,
                'cliente': vendedor if tipo == 'venta' else 'Cliente desde PDF',
                'items': [{
                    'descripcion': producto,
                    'cantidad': precios['cantidad'],
                    'precio': precios['precio_unitario']
                }],
                'subtotal': precios['subtotal'],
                'impuestos': impuestos,
                'total': precios['total']
            }
            
            self.logger.info(f"Datos extraídos - Tipo: {tipo}, Total: ${datos['total']:,.2f}")
            return datos
            
        except Exception as e:
            self.logger.error(f"Error procesando PDF: {e}")
            return None
    
    def detect_invoice_type(self, texto):
        """Detectar automáticamente si es factura de compra o venta"""
        texto_lower = texto.lower()
        
        # Keywords para compra
        compra_keywords = self.config.get('parsing', {}).get('keywords_compra', 
            ['proveedor', 'compra', 'bill', 'invoice', 'factura de compra'])
        
        # Keywords para venta
        venta_keywords = self.config.get('parsing', {}).get('keywords_venta', 
            ['cliente', 'venta', 'sale', 'factura de venta'])
        
        compra_score = sum(1 for keyword in compra_keywords if keyword in texto_lower)
        venta_score = sum(1 for keyword in venta_keywords if keyword in texto_lower)
        
        # Patrones específicos
        if 'factura electrónica de venta' in texto_lower:
            return 'compra'  # Es una factura que recibimos (compra)
        elif 'factura de venta' in texto_lower:
            return 'venta'   # Es una factura que emitimos (venta)
        
        # Decisión basada en scores
        if compra_score > venta_score:
            return 'compra'
        elif venta_score > compra_score:
            return 'venta'
        else:
            # Por defecto, asumir compra si no se puede determinar
            self.logger.warning("No se pudo determinar el tipo de factura, asumiendo compra")
            return 'compra'
    
    def extract_date(self, texto):
        """Extraer fecha del texto"""
        date_patterns = [
            r'Fecha:\s*(\d{1,2}-\d{1,2}-\d{4})',
            r'Fecha:\s*(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}-\d{1,2}-\d{4})',
            r'(\d{4}-\d{2}-\d{2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, texto)
            if match:
                fecha_str = match.group(1)
                return self.format_date(fecha_str)
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def format_date(self, fecha_str):
        """Formatear fecha a YYYY-MM-DD"""
        try:
            # Intentar diferentes formatos
            formats = ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d']
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(fecha_str, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # Si no coincide con ningún formato, devolver tal como está
            return fecha_str
        except:
            return datetime.now().strftime('%Y-%m-%d')
    
    def extract_vendor(self, texto):
        """Extraer vendedor/proveedor del texto"""
        patterns = [
            r'Factura electrónica de venta #\d+\n([^\n]+)',
            r'Proveedor[:\s]+(.+)',
            r'Vendedor[:\s]+(.+)',
            r'Cliente[:\s]+(.+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Proveedor Desconocido"
    
    def extract_product(self, texto):
        """Extraer producto del texto"""
        patterns = [
            r'(\d+)\s*-\s*(.+?)\s*Impuestos:',
            r'Producto[:\s]+(.+)',
            r'Descripción[:\s]+(.+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto, re.DOTALL | re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    codigo, descripcion = match.groups()
                    return f"{codigo} - {descripcion.strip()}"
                else:
                    return match.group(1).strip()
        
        return "Producto no identificado"
    
    def extract_prices(self, texto):
        """Extraer precios del texto"""
        # Precio unitario
        price_match = re.search(r'Precio unit\.\s*\$?([\d,]+\.?\d*)', texto)
        precio_unitario = float(price_match.group(1).replace(',', '')) if price_match else 0.0
        
        # Cantidad
        qty_match = re.search(r'(\d+)\s+Unidad', texto)
        cantidad = float(qty_match.group(1)) if qty_match else 1.0
        
        # Subtotal
        subtotal_match = re.search(r'Subtotal\s+\$?([\d,]+\.?\d*)', texto)
        subtotal = float(subtotal_match.group(1).replace(',', '')) if subtotal_match else precio_unitario
        
        # Total
        total_patterns = [
            r'Total[:\s]+\d+\s+Unidad\s+\$?([\d,]+\.?\d*)',
            r'Total[:\s]+\$?([\d,]+\.?\d*)',
            r'Valor Total[:\s]+\$?([\d,]+\.?\d*)'
        ]
        
        total = 0.0
        for pattern in total_patterns:
            match = re.search(pattern, texto)
            if match:
                total = float(match.group(1).replace(',', ''))
                break
        
        return {
            'precio_unitario': precio_unitario,
            'cantidad': cantidad,
            'subtotal': subtotal,
            'total': total
        }
    
    def extract_taxes(self, texto):
        """Extraer impuestos del texto"""
        patterns = [
            r'Impuestos\s+\$?([\d,]+\.?\d*)',
            r'IVA\s+\$?([\d,]+\.?\d*)',
            r'Tax[:\s]+\$?([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto)
            if match:
                return float(match.group(1).replace(',', ''))
        
        return 0.0
    
    def get_or_create_contact(self, name, contact_type='client'):
        """Obtener o crear contacto en Alegra"""
        try:
            # Buscar contacto existente
            response = requests.get(f'{self.base_url}/contacts', 
                                 params={'query': name}, 
                                 headers=self.headers, 
                                 timeout=10)
            
            if response.status_code == 200:
                contacts = response.json()
                for contact in contacts:
                    if contact.get('name', '').lower() == name.lower():
                        self.logger.info(f"Contacto encontrado: {name} (ID: {contact.get('id')})")
                        return contact.get('id')
            
            # Si no se encuentra, usar contacto existente como fallback
            self.logger.warning(f"Contacto '{name}' no encontrado, usando contacto existente")
            
            # Buscar cualquier contacto existente
            response = requests.get(f'{self.base_url}/contacts', 
                                 headers=self.headers, 
                                 timeout=10)
            
            if response.status_code == 200:
                contacts = response.json()
                if contacts:
                    fallback_contact = contacts[0]
                    self.logger.info(f"Usando contacto existente: {fallback_contact.get('name')} (ID: {fallback_contact.get('id')})")
                    return fallback_contact.get('id')
            
            self.logger.error("No se encontraron contactos en Alegra")
            return None
                
        except Exception as e:
            self.logger.error(f"Error con contactos: {e}")
            return None
    
    def get_or_create_item(self, name, price):
        """Obtener o crear item en Alegra"""
        try:
            # Buscar item existente
            response = requests.get(f'{self.base_url}/items', 
                                 params={'query': name}, 
                                 headers=self.headers, 
                                 timeout=10)
            
            if response.status_code == 200:
                items = response.json()
                for item in items:
                    if item.get('name', '').lower() == name.lower():
                        self.logger.info(f"Item encontrado: {name} (ID: {item.get('id')})")
                        return item.get('id')
            
            # Crear nuevo item
            self.logger.info(f"Creando nuevo item: {name}")
            item_data = {
                "name": name,
                "price": price,
                "description": f"Producto procesado desde PDF - {name}"
            }
            
            response = requests.post(f'{self.base_url}/items', 
                                   json=item_data, 
                                   headers=self.headers, 
                                   timeout=10)
            
            if response.status_code == 201:
                created_item = response.json()
                self.logger.info(f"Item creado: {name} (ID: {created_item.get('id')})")
                return created_item.get('id')
            else:
                self.logger.error(f"Error creando item: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error con items: {e}")
            return None
    
    def create_purchase_bill(self, datos_factura):
        """Crear factura de compra (bill) en Alegra"""
        self.logger.info("Creando factura de COMPRA en Alegra...")
        
        try:
            # Obtener o crear proveedor
            provider_id = self.get_or_create_contact(datos_factura['proveedor'], 'provider')
            if not provider_id:
                self.logger.error("No se pudo obtener/crear proveedor")
                return None
            
            # Obtener o crear items
            items = []
            for item in datos_factura['items']:
                item_id = self.get_or_create_item(item['descripcion'], item['precio'])
                if item_id:
                    items.append({
                        "id": item_id,
                        "quantity": item['cantidad'],
                        "price": item['precio']
                    })
            
            if not items:
                self.logger.error("No se pudieron obtener items válidos")
                return None
            
            # Crear bill
            payload = {
                "date": datos_factura['fecha'],
                "dueDate": datos_factura['fecha'],
                "provider": {"id": provider_id},
                "items": items,
                "total": datos_factura['total'],
                "observations": f"Compra procesada desde PDF - {datos_factura['proveedor']} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "accountingAccount": {"id": 1}  # Cuenta contable por defecto
            }
            
            response = requests.post(f'{self.base_url}/bills', 
                                   json=payload, 
                                   headers=self.headers, 
                                   timeout=30)
            
            if response.status_code == 201:
                bill = response.json()
                self.logger.info(f"Bill creada exitosamente: ID {bill.get('id')}")
                return bill
            else:
                self.logger.error(f"Error creando bill: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error en create_purchase_bill: {e}")
            return None
    
    def create_sale_invoice(self, datos_factura):
        """Crear factura de venta en Alegra"""
        self.logger.info("Creando factura de VENTA en Alegra...")
        
        try:
            # Obtener o crear cliente
            client_id = self.get_or_create_contact(datos_factura['cliente'], 'client')
            if not client_id:
                self.logger.error("No se pudo obtener/crear cliente")
                return None
            
            # Obtener o crear items
            items = []
            for item in datos_factura['items']:
                item_id = self.get_or_create_item(item['descripcion'], item['precio'])
                if item_id:
                    items.append({
                        "id": item_id,
                        "quantity": item['cantidad'],
                        "price": item['precio']
                    })
            
            if not items:
                self.logger.error("No se pudieron obtener items válidos")
                return None
            
            # Calcular fecha de vencimiento
            fecha_vencimiento = datetime.strptime(datos_factura['fecha'], '%Y-%m-%d') + timedelta(days=30)
            
            # Crear invoice
            payload = {
                "date": datos_factura['fecha'],
                "dueDate": fecha_vencimiento.strftime('%Y-%m-%d'),
                "client": {"id": client_id},
                "items": items,
                "total": datos_factura['total'],
                "observations": f"Venta procesada desde PDF - {datos_factura['cliente']} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            }
            
            response = requests.post(f'{self.base_url}/invoices', 
                                   json=payload, 
                                   headers=self.headers, 
                                   timeout=30)
            
            if response.status_code == 201:
                invoice = response.json()
                self.logger.info(f"Invoice creada exitosamente: ID {invoice.get('id')}")
                return invoice
            else:
                self.logger.error(f"Error creando invoice: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error en create_sale_invoice: {e}")
            return None
    
    def register_local_purchase(self, datos_factura):
        """Registrar compra localmente como backup"""
        try:
            registro_file = f"backup/facturas_compra_{datetime.now().strftime('%Y%m%d')}.txt"
            
            registro_entry = f"""
FACTURA DE COMPRA REGISTRADA
============================
Fecha: {datos_factura['fecha']}
Proveedor: {datos_factura['proveedor']}
Producto: {datos_factura['items'][0]['descripcion']}
Cantidad: {datos_factura['items'][0]['cantidad']}
Precio Unitario: ${datos_factura['items'][0]['precio']:,.2f}
Subtotal: ${datos_factura['subtotal']:,.2f}
Impuestos: ${datos_factura['impuestos']:,.2f}
Total: ${datos_factura['total']:,.2f}
Registrado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
============================
"""
            
            with open(registro_file, 'a', encoding='utf-8') as f:
                f.write(registro_entry)
            
            self.logger.info(f"Compra registrada localmente en {registro_file}")
            
        except Exception as e:
            self.logger.error(f"Error registrando compra local: {e}")
    
    def process_invoice(self, pdf_path):
        """Procesar factura completa"""
        self.logger.info(f"Iniciando procesamiento de: {pdf_path}")
        
        # Extraer datos
        datos = self.extract_data_from_pdf(pdf_path)
        if not datos:
            self.logger.error("No se pudieron extraer datos del PDF")
            return False
        
        # Procesar según tipo
        if datos['tipo'] == 'compra':
            resultado = self.create_purchase_bill(datos)
            if resultado:
                self.register_local_purchase(datos)
                self.logger.info("✅ Factura de COMPRA procesada exitosamente")
                return True
        else:  # venta
            resultado = self.create_sale_invoice(datos)
            if resultado:
                self.logger.info("✅ Factura de VENTA procesada exitosamente")
                return True
        
        self.logger.error("❌ Error procesando factura")
        return False

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='InvoiceBot v2.0 - Bot Contable Integral')
    parser.add_argument('pdf_path', help='Ruta al archivo PDF a procesar')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo verbose')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Verificar que el archivo existe
    if not os.path.exists(args.pdf_path):
        print(f"❌ Archivo no encontrado: {args.pdf_path}")
        sys.exit(1)
    
    # Crear instancia del bot
    try:
        bot = InvoiceBot()
        success = bot.process_invoice(args.pdf_path)
        
        if success:
            print("🎉 ¡Factura procesada exitosamente!")
        else:
            print("❌ Error procesando factura")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error inicializando bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()