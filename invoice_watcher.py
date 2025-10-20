#!/usr/bin/env python3
"""
Sistema de monitoreo automático de facturas
Monitorea una carpeta y procesa automáticamente PDFs nuevos
"""

import os
import time
import logging
from typing import Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from invoice_processor_enhanced import InvoiceProcessor
from datetime import datetime

class InvoiceHandler(FileSystemEventHandler):
    """Manejador de eventos para archivos de facturas"""
    
    def __init__(self, watch_folder: str, processed_folder: str = None, 
                 high_amount_threshold: float = 1000000, 
                 use_nanobot: bool = False):
        self.watch_folder = watch_folder
        self.processed_folder = processed_folder or os.path.join(watch_folder, 'processed')
        self.processor = InvoiceProcessor()
        self.high_amount_threshold = high_amount_threshold
        self.use_nanobot = use_nanobot
        
        # Crear carpetas necesarias
        os.makedirs(self.processed_folder, exist_ok=True)
        os.makedirs(os.path.join(watch_folder, 'high_amount'), exist_ok=True)
        os.makedirs(os.path.join(watch_folder, 'error'), exist_ok=True)
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        # Archivos en proceso para evitar procesamiento duplicado
        self.processing_files = set()
        
        # Configurar Nanobot si está habilitado
        self.nanobot_client = None
        if use_nanobot:
            try:
                from nanobot_client import NanobotClient
                self.nanobot_client = NanobotClient('http://localhost:8080')
                self.logger.info("🤖 Nanobot habilitado para notificaciones")
            except Exception as e:
                self.logger.warning(f"⚠️ No se pudo conectar a Nanobot: {e}")
                self.nanobot_client = None
    
    def on_created(self, event):
        """Se ejecuta cuando se crea un archivo"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # Procesar archivos PDF, JPG y PNG
        file_ext = file_path.lower().split('.')[-1]
        if file_ext not in ['pdf', 'jpg', 'jpeg', 'png']:
            return
        
        # Evitar procesamiento duplicado
        if file_path in self.processing_files:
            return
        
        self.logger.info(f"📁 Nuevo archivo detectado: {file_path}")
        
        # Esperar un poco para asegurar que el archivo esté completamente escrito
        time.sleep(2)
        
        # Verificar que el archivo existe y no está siendo usado
        if not os.path.exists(file_path):
            return
        
        try:
            # Procesar el archivo
            self.process_invoice(file_path)
        except Exception as e:
            self.logger.error(f"❌ Error procesando {file_path}: {e}")
        finally:
            # Remover de archivos en proceso
            self.processing_files.discard(file_path)
    
    def process_invoice(self, file_path: str):
        """Procesar una factura individual con validaciones de monto"""
        self.logger.info(f"🔄 Procesando factura: {file_path}")
        
        try:
            # Extraer datos del archivo (PDF o imagen)
            datos = self.processor.process_invoice_file(file_path)
            
            if not datos:
                self.logger.error(f"❌ No se pudieron extraer datos de {file_path}")
                self.move_to_error_folder(file_path)
                return
            
            # Validar monto alto
            total = datos.get('total', 0)
            if total > self.high_amount_threshold:
                self.logger.warning(f"🚨 MONTO ALTO DETECTADO: ${total:,.2f} en {file_path}")
                self.handle_high_amount_invoice(file_path, datos)
                return
            
            # Procesar según el tipo detectado
            if datos['tipo'] == 'compra':
                # Crear bill en Alegra
                resultado = self.processor.create_purchase_bill(datos)
                if resultado:
                    # También registrar localmente como backup
                    self.processor.register_local_purchase(datos)
                    self.logger.info(f"✅ Factura de COMPRA procesada: {file_path}")
                    self.move_to_processed_folder(file_path, 'compra')
                else:
                    self.logger.error(f"❌ Error procesando factura de compra: {file_path}")
                    self.move_to_error_folder(file_path)
            else:  # venta
                resultado = self.processor.create_sale_invoice(datos)
                if resultado:
                    self.logger.info(f"✅ Factura de VENTA procesada: {file_path}")
                    self.move_to_processed_folder(file_path, 'venta')
                else:
                    self.logger.error(f"❌ Error procesando factura de venta: {file_path}")
                    self.move_to_error_folder(file_path)
                    
        except Exception as e:
            self.logger.error(f"❌ Error procesando {file_path}: {e}")
            self.move_to_error_folder(file_path)
    
    def move_to_processed_folder(self, file_path: str, invoice_type: str):
        """Mover archivo a carpeta de procesados"""
        try:
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{timestamp}_{invoice_type}_{filename}"
            
            processed_path = os.path.join(self.processed_folder, new_filename)
            
            os.rename(file_path, processed_path)
            self.logger.info(f"📁 Archivo movido a procesados: {processed_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Error moviendo archivo: {e}")
    
    def move_to_error_folder(self, file_path: str):
        """Mover archivo a carpeta de errores"""
        try:
            error_folder = os.path.join(self.watch_folder, 'error')
            os.makedirs(error_folder, exist_ok=True)
            
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{timestamp}_error_{filename}"
            
            error_path = os.path.join(error_folder, new_filename)
            
            os.rename(file_path, error_path)
            self.logger.info(f"📁 Archivo movido a errores: {error_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Error moviendo archivo a errores: {e}")
    
    def handle_high_amount_invoice(self, file_path: str, datos: Dict):
        """Manejar facturas de monto alto"""
        total = datos.get('total', 0)
        
        # Mover a carpeta de monto alto
        high_amount_folder = os.path.join(self.watch_folder, 'high_amount')
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_filename = f"{timestamp}_high_{total:,.0f}_{filename}"
        
        try:
            high_amount_path = os.path.join(high_amount_folder, new_filename)
            os.rename(file_path, high_amount_path)
            self.logger.info(f"📁 Factura de monto alto movida: {high_amount_path}")
            
            # Notificar via Nanobot si está disponible
            if self.nanobot_client:
                self.notify_high_amount_invoice(high_amount_path, datos)
            else:
                self.logger.warning(f"⚠️ Factura de monto alto requiere revisión manual: ${total:,.2f}")
                
        except Exception as e:
            self.logger.error(f"❌ Error manejando factura de monto alto: {e}")
    
    def notify_high_amount_invoice(self, file_path: str, datos: Dict):
        """Notificar factura de monto alto via Nanobot"""
        try:
            notification = {
                'type': 'high_amount_invoice',
                'file_path': file_path,
                'total': datos.get('total', 0),
                'tipo': datos.get('tipo', 'unknown'),
                'fecha': datos.get('fecha', 'unknown'),
                'timestamp': datetime.now().isoformat()
            }
            
            response = self.nanobot_client.triage_invoice(
                'invoice_triage',
                notification
            )
            
            if response.get('success'):
                self.logger.info("✅ Notificación enviada a Nanobot")
            else:
                self.logger.warning("⚠️ No se pudo enviar notificación a Nanobot")
                
        except Exception as e:
            self.logger.error(f"❌ Error enviando notificación: {e}")

class InvoiceWatcher:
    """Sistema de monitoreo de facturas"""
    
    def __init__(self, watch_folder: str, high_amount_threshold: float = 1000000, 
                 use_nanobot: bool = False):
        self.watch_folder = watch_folder
        self.observer = Observer()
        self.handler = InvoiceHandler(watch_folder, 
                                    high_amount_threshold=high_amount_threshold,
                                    use_nanobot=use_nanobot)
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        # Verificar que la carpeta existe
        if not os.path.exists(watch_folder):
            os.makedirs(watch_folder, exist_ok=True)
            self.logger.info(f"📁 Carpeta creada: {watch_folder}")
        
        self.logger.info(f"💰 Threshold de monto alto: ${high_amount_threshold:,.2f}")
        if use_nanobot:
            self.logger.info("🤖 Nanobot habilitado para notificaciones")
    
    def start(self):
        """Iniciar monitoreo"""
        self.logger.info(f"🚀 Iniciando monitoreo de carpeta: {self.watch_folder}")
        
        self.observer.schedule(self.handler, self.watch_folder, recursive=False)
        self.observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Detener monitoreo"""
        self.logger.info("🛑 Deteniendo monitoreo...")
        self.observer.stop()
        self.observer.join()

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitoreo automático de facturas')
    parser.add_argument('watch_folder', help='Carpeta a monitorear')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Nivel de logging')
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/invoice_watcher.log'),
            logging.StreamHandler()
        ]
    )
    
    # Crear y ejecutar watcher
    watcher = InvoiceWatcher(args.watch_folder)
    watcher.start()

if __name__ == "__main__":
    main()