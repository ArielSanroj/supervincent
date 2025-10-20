import requests
import base64
import xml.etree.ElementTree as ET
import pdfplumber
import os
import re
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('invoice_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
ALEGRA_USER = os.getenv('ALEGRA_USER')
ALEGRA_TOKEN = os.getenv('ALEGRA_TOKEN')
ALEGRA_BASE_URL = 'https://api.alegra.com/api/v1'

class InvoiceProcessor:
    def __init__(self):
        self.alegra_user = ALEGRA_USER
        self.alegra_token = ALEGRA_TOKEN
        self.base_url = ALEGRA_BASE_URL
        
        if not self.alegra_user or not self.alegra_token:
            raise ValueError("ALEGRA_USER y ALEGRA_TOKEN deben estar configurados en el archivo .env")
    
    def parsear_factura_xml(self, archivo_xml):
        """Parsear factura XML (CFDI, DIAN, etc.)"""
        try:
            tree = ET.parse(archivo_xml)
            root = tree.getroot()
            
            # Namespace handling para CFDI
            namespaces = {
                'cfdi': 'http://www.sat.gob.mx/cfd/3',
                'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
            }
            
            # Extraer datos básicos
            fecha = self._extract_xml_value(root, './/cfdi:Comprobante/@Fecha', namespaces)
            if not fecha:
                fecha = self._extract_xml_value(root, './/fecha')
            
            cliente_nombre = self._extract_xml_value(root, './/cfdi:Receptor/@Nombre', namespaces)
            if not cliente_nombre:
                cliente_nombre = self._extract_xml_value(root, './/cliente/nombre')
            
            # Extraer items
            items = []
            conceptos = root.findall('.//cfdi:Concepto', namespaces)
            if not conceptos:
                conceptos = root.findall('.//items/item')
            
            for concepto in conceptos:
                descripcion = self._extract_xml_value(concepto, './@Descripcion', namespaces)
                if not descripcion:
                    descripcion = self._extract_xml_value(concepto, './descripcion')
                
                cantidad = self._extract_xml_value(concepto, './@Cantidad', namespaces)
                if not cantidad:
                    cantidad = self._extract_xml_value(concepto, './cantidad')
                
                precio = self._extract_xml_value(concepto, './@ValorUnitario', namespaces)
                if not precio:
                    precio = self._extract_xml_value(concepto, './precio')
                
                if descripcion and cantidad and precio:
                    items.append({
                        'descripcion': descripcion,
                        'cantidad': float(cantidad),
                        'precio': float(precio)
                    })
            
            # Extraer total
            total = self._extract_xml_value(root, './/cfdi:Comprobante/@Total', namespaces)
            if not total:
                total = self._extract_xml_value(root, './/total')
            
            if not total:
                # Calcular total si no se encuentra
                total = sum(item['cantidad'] * item['precio'] for item in items)
            
            return {
                'fecha': fecha,
                'cliente': cliente_nombre,
                'items': items,
                'total': float(total) if total else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error parseando XML {archivo_xml}: {e}")
            return None
    
    def _extract_xml_value(self, element, xpath, namespaces=None):
        """Extraer valor de XML con manejo de namespaces"""
        try:
            result = element.find(xpath, namespaces)
            return result.text if result is not None else None
        except:
            return None
    
    def parsear_factura_pdf(self, archivo_pdf):
        """Parsear factura PDF con patrones mejorados"""
        try:
            with pdfplumber.open(archivo_pdf) as pdf:
                texto = ''
                for page in pdf.pages:
                    texto += page.extract_text() or ''
            
            # Patrones de regex mejorados
            fecha_patterns = [
                r'Fecha[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ]
            
            cliente_patterns = [
                r'Cliente[:\s]+(.+)',
                r'Customer[:\s]+(.+)',
                r'Facturar a[:\s]+(.+)',
                r'Bill to[:\s]+(.+)'
            ]
            
            total_patterns = [
                r'Total[:\s]+\$?([\d,]+\.?\d*)',
                r'Amount[:\s]+\$?([\d,]+\.?\d*)',
                r'Subtotal[:\s]+\$?([\d,]+\.?\d*)'
            ]
            
            # Extraer datos
            fecha = self._extract_with_patterns(texto, fecha_patterns)
            cliente = self._extract_with_patterns(texto, cliente_patterns)
            total = self._extract_with_patterns(texto, total_patterns)
            
            # Extraer items (patrón básico)
            items = self._extract_items_from_pdf(texto)
            
            return {
                'fecha': fecha or datetime.now().strftime('%Y-%m-%d'),
                'cliente': cliente or 'Cliente Desconocido',
                'items': items,
                'total': float(total.replace(',', '')) if total else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error parseando PDF {archivo_pdf}: {e}")
            return None
    
    def _extract_with_patterns(self, text, patterns):
        """Extraer texto usando múltiples patrones"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_items_from_pdf(self, text):
        """Extraer items de PDF (implementación básica)"""
        items = []
        lines = text.split('\n')
        
        # Buscar tabla de items
        in_items_section = False
        for line in lines:
            if 'descripcion' in line.lower() or 'item' in line.lower():
                in_items_section = True
                continue
            
            if in_items_section and line.strip():
                # Patrón básico para extraer items
                parts = re.split(r'\s+', line.strip())
                if len(parts) >= 3:
                    try:
                        descripcion = ' '.join(parts[:-2])
                        cantidad = float(parts[-2])
                        precio = float(parts[-1].replace(',', ''))
                        items.append({
                            'descripcion': descripcion,
                            'cantidad': cantidad,
                            'precio': precio
                        })
                    except ValueError:
                        continue
        
        return items
    
    def crear_factura_alegra(self, datos_factura):
        """Crear factura en Alegra"""
        auth = base64.b64encode(f"{self.alegra_user}:{self.alegra_token}".encode()).decode()
        headers = {
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/json'
        }
        
        # Calcular fecha de vencimiento (30 días después)
        fecha_vencimiento = datetime.strptime(datos_factura['fecha'], '%Y-%m-%d') + timedelta(days=30)
        
        payload = {
            "date": datos_factura['fecha'],
            "dueDate": fecha_vencimiento.strftime('%Y-%m-%d'),
            "client": {"name": datos_factura['cliente']},
            "items": [
                {
                    "name": item['descripcion'],
                    "quantity": item['cantidad'],
                    "price": item['precio']
                } for item in datos_factura['items']
            ],
            "observations": "Factura procesada automáticamente por InvoiceBot"
        }
        
        try:
            response = requests.post(f'{self.base_url}/invoices', json=payload, headers=headers)
            
            if response.status_code == 201:
                factura_creada = response.json()
                logger.info(f"Factura creada exitosamente: {factura_creada.get('id')}")
                return factura_creada
            else:
                logger.error(f"Error creando factura: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error en API Alegra: {e}")
            return None
    
    def procesar_factura(self, archivo, tipo='xml'):
        """Procesar factura según el tipo"""
        logger.info(f"Procesando factura: {archivo} (tipo: {tipo})")
        
        # Seleccionar parser según tipo
        if tipo.lower() == 'xml':
            datos = self.parsear_factura_xml(archivo)
        elif tipo.lower() == 'pdf':
            datos = self.parsear_factura_pdf(archivo)
        else:
            logger.error(f"Tipo de archivo no soportado: {tipo}")
            return None
        
        if datos:
            logger.info(f"Datos extraídos: {datos}")
            return self.crear_factura_alegra(datos)
        else:
            logger.error("No se pudieron extraer datos de la factura")
            return None

class InvoiceFileHandler(FileSystemEventHandler):
    """Manejador de archivos para procesamiento automático"""
    
    def __init__(self, processor):
        self.processor = processor
        self.processed_files = set()
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        file_ext = Path(file_path).suffix.lower()
        
        # Evitar procesar archivos temporales
        if file_path.endswith('.tmp') or file_path.endswith('~'):
            return
        
        # Procesar después de un pequeño delay para asegurar que el archivo esté completamente escrito
        import time
        time.sleep(1)
        
        if file_ext == '.xml':
            self.processor.procesar_factura(file_path, 'xml')
        elif file_ext == '.pdf':
            self.processor.procesar_factura(file_path, 'pdf')

def monitorear_carpeta(carpeta_facturas):
    """Monitorear carpeta para procesar facturas automáticamente"""
    processor = InvoiceProcessor()
    event_handler = InvoiceFileHandler(processor)
    observer = Observer()
    
    observer.schedule(event_handler, carpeta_facturas, recursive=False)
    observer.start()
    
    logger.info(f"Monitoreando carpeta: {carpeta_facturas}")
    
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Procesador de Facturas para Alegra')
    parser.add_argument('--archivo', help='Archivo de factura a procesar')
    parser.add_argument('--tipo', choices=['xml', 'pdf'], default='xml', help='Tipo de archivo')
    parser.add_argument('--monitor', help='Carpeta a monitorear para procesamiento automático')
    
    args = parser.parse_args()
    
    if args.monitor:
        monitorear_carpeta(args.monitor)
    elif args.archivo:
        processor = InvoiceProcessor()
        resultado = processor.procesar_factura(args.archivo, args.tipo)
        if resultado:
            print("✅ Factura procesada exitosamente")
        else:
            print("❌ Error procesando factura")
    else:
        print("Usa --help para ver las opciones disponibles")

if __name__ == "__main__":
    main()