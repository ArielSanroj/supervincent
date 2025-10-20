#!/usr/bin/env python3
"""
Sistema de monitoreo de facturas con procesamiento asíncrono
"""

import os
import time
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from tasks import process_invoice, sync_alegra_data
from cache_manager import CacheManager

class AsyncInvoiceHandler(FileSystemEventHandler):
    """Manejador asíncrono de eventos para archivos de facturas"""
    
    def __init__(self, watch_folder: str, processed_folder: str = None, 
                 high_amount_threshold: float = 1000000, 
                 use_nanobot: bool = False,
                 use_cache: bool = True):
        self.watch_folder = watch_folder
        self.processed_folder = processed_folder or os.path.join(watch_folder, 'processed')
        self.high_amount_threshold = high_amount_threshold
        self.use_nanobot = use_nanobot
        self.use_cache = use_cache
        
        # Crear carpetas necesarias
        os.makedirs(self.processed_folder, exist_ok=True)
        os.makedirs(os.path.join(watch_folder, 'high_amount'), exist_ok=True)
        os.makedirs(os.path.join(watch_folder, 'error'), exist_ok=True)
        os.makedirs(os.path.join(watch_folder, 'pending'), exist_ok=True)
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        # Inicializar cache manager si está habilitado
        self.cache_manager = CacheManager() if use_cache else None
        
        # Archivos en proceso para evitar procesamiento duplicado
        self.processing_files = set()
        
        # Estadísticas
        self.stats = {
            'processed': 0,
            'errors': 0,
            'high_amount': 0,
            'cached_hits': 0,
            'cache_misses': 0
        }
    
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
        
        # Procesar de forma asíncrona
        self.process_invoice_async(file_path)
    
    def process_invoice_async(self, file_path: str):
        """Procesar factura de forma asíncrona"""
        try:
            # Mover a carpeta de pendientes
            pending_folder = os.path.join(self.watch_folder, 'pending')
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pending_filename = f"{timestamp}_{filename}"
            pending_path = os.path.join(pending_folder, pending_filename)
            
            # Mover archivo
            os.rename(file_path, pending_path)
            
            # Enviar tarea a cola
            task = process_invoice.delay(pending_path, self.use_nanobot)
            
            # Registrar archivo en proceso
            self.processing_files.add(pending_path)
            
            self.logger.info(f"🔄 Tarea enviada a cola: {task.id} para {pending_path}")
            
            # Actualizar estadísticas
            self.stats['processed'] += 1
            
        except Exception as e:
            self.logger.error(f"❌ Error enviando tarea a cola: {e}")
            self.move_to_error_folder(file_path)
            self.stats['errors'] += 1
    
    def check_task_status(self, task_id: str) -> dict:
        """Verificar estado de una tarea"""
        try:
            from celery.result import AsyncResult
            result = AsyncResult(task_id)
            
            return {
                'id': task_id,
                'status': result.status,
                'result': result.result if result.ready() else None,
                'info': result.info if hasattr(result, 'info') else None
            }
        except Exception as e:
            self.logger.error(f"❌ Error verificando estado de tarea: {e}")
            return {'id': task_id, 'status': 'UNKNOWN', 'error': str(e)}
    
    def get_processing_stats(self) -> dict:
        """Obtener estadísticas de procesamiento"""
        stats = self.stats.copy()
        
        if self.cache_manager:
            cache_stats = self.cache_manager.get_cache_stats()
            stats['cache'] = cache_stats
        
        stats['files_in_process'] = len(self.processing_files)
        stats['timestamp'] = datetime.now().isoformat()
        
        return stats
    
    def move_to_error_folder(self, file_path: str):
        """Mover archivo a carpeta de errores"""
        try:
            error_folder = os.path.join(self.watch_folder, 'error')
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{timestamp}_error_{filename}"
            
            error_path = os.path.join(error_folder, new_filename)
            os.rename(file_path, error_path)
            
            self.logger.info(f"📁 Archivo movido a errores: {error_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Error moviendo archivo a errores: {e}")
    
    def cleanup_processed_files(self, days_old: int = 7):
        """Limpiar archivos procesados antiguos"""
        try:
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            cleaned_count = 0
            
            # Limpiar carpeta de procesados
            if os.path.exists(self.processed_folder):
                for filename in os.listdir(self.processed_folder):
                    file_path = os.path.join(self.processed_folder, filename)
                    if os.path.isfile(file_path):
                        if os.path.getmtime(file_path) < cutoff_time:
                            os.remove(file_path)
                            cleaned_count += 1
            
            self.logger.info(f"🧹 Limpieza completada: {cleaned_count} archivos eliminados")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"❌ Error en limpieza: {e}")
            return 0

class AsyncInvoiceWatcher:
    """Sistema de monitoreo asíncrono de facturas"""
    
    def __init__(self, watch_folder: str, high_amount_threshold: float = 1000000, 
                 use_nanobot: bool = False, use_cache: bool = True):
        self.watch_folder = watch_folder
        self.observer = Observer()
        self.handler = AsyncInvoiceHandler(
            watch_folder, 
            high_amount_threshold=high_amount_threshold,
            use_nanobot=use_nanobot,
            use_cache=use_cache
        )
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        # Verificar que la carpeta existe
        if not os.path.exists(watch_folder):
            os.makedirs(watch_folder, exist_ok=True)
            self.logger.info(f"📁 Carpeta creada: {watch_folder}")
        
        self.logger.info(f"💰 Threshold de monto alto: ${high_amount_threshold:,.2f}")
        if use_nanobot:
            self.logger.info("🤖 Nanobot habilitado para notificaciones")
        if use_cache:
            self.logger.info("💾 Caché habilitado para optimización")
    
    def start(self):
        """Iniciar monitoreo asíncrono"""
        self.logger.info(f"🚀 Iniciando monitoreo asíncrono de carpeta: {self.watch_folder}")
        
        # Sincronizar datos de Alegra al inicio
        if self.handler.use_cache:
            self.logger.info("🔄 Sincronizando datos de Alegra...")
            try:
                sync_alegra_data.delay('contacts')
                sync_alegra_data.delay('accounts')
            except Exception as e:
                self.logger.warning(f"⚠️ Error sincronizando datos: {e}")
        
        self.observer.schedule(self.handler, self.watch_folder, recursive=False)
        self.observer.start()
        
        try:
            while True:
                time.sleep(1)
                
                # Mostrar estadísticas cada 60 segundos
                if int(time.time()) % 60 == 0:
                    stats = self.handler.get_processing_stats()
                    self.logger.info(f"📊 Estadísticas: {stats}")
                    
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Detener monitoreo"""
        self.logger.info("🛑 Deteniendo monitoreo asíncrono...")
        self.observer.stop()
        self.observer.join()
    
    def get_stats(self) -> dict:
        """Obtener estadísticas del watcher"""
        return self.handler.get_processing_stats()

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema de monitoreo asíncrono de facturas')
    parser.add_argument('--watch-folder', required=True, help='Carpeta a monitorear')
    parser.add_argument('--high-amount-threshold', type=float, default=1000000, 
                       help='Threshold para montos altos')
    parser.add_argument('--use-nanobot', action='store_true', 
                       help='Usar Nanobot para validaciones')
    parser.add_argument('--use-cache', action='store_true', default=True,
                       help='Usar caché para optimización')
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        watcher = AsyncInvoiceWatcher(
            args.watch_folder,
            high_amount_threshold=args.high_amount_threshold,
            use_nanobot=args.use_nanobot,
            use_cache=args.use_cache
        )
        
        watcher.start()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()