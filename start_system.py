#!/usr/bin/env python3
"""
Script de inicio para el sistema completo de facturas con optimizaciones
"""

import os
import sys
import time
import subprocess
import signal
import logging
from datetime import datetime
from pathlib import Path

class InvoiceSystemManager:
    """Gestor del sistema completo de facturas"""
    
    def __init__(self):
        self.processes = {}
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Configurar logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('system.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def start_redis(self):
        """Iniciar Redis si no está corriendo"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            self.logger.info("✅ Redis ya está corriendo")
            return True
        except:
            self.logger.warning("⚠️ Redis no está disponible. Asegúrate de que esté instalado y corriendo.")
            return False
    
    def start_celery_worker(self, concurrency: int = 4):
        """Iniciar worker de Celery"""
        try:
            cmd = [
                'celery', '-A', 'celery_config', 'worker',
                '--loglevel=info',
                f'--concurrency={concurrency}',
                '--queues=invoice_processing,report_generation,tax_validation,alegra_sync'
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            self.processes['celery_worker'] = process
            self.logger.info(f"✅ Worker de Celery iniciado (PID: {process.pid})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando worker de Celery: {e}")
            return False
    
    def start_celery_beat(self):
        """Iniciar scheduler de Celery"""
        try:
            cmd = ['celery', '-A', 'celery_config', 'beat', '--loglevel=info']
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            self.processes['celery_beat'] = process
            self.logger.info(f"✅ Scheduler de Celery iniciado (PID: {process.pid})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando scheduler de Celery: {e}")
            return False
    
    def start_flower(self, port: int = 5555):
        """Iniciar Flower para monitoreo"""
        try:
            cmd = ['celery', '-A', 'celery_config', 'flower', f'--port={port}']
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            self.processes['flower'] = process
            self.logger.info(f"✅ Flower iniciado en puerto {port} (PID: {process.pid})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando Flower: {e}")
            return False
    
    def start_invoice_watcher(self, watch_folder: str, use_nanobot: bool = False):
        """Iniciar watcher de facturas"""
        try:
            cmd = [
                'python', 'invoice_watcher_async.py',
                '--watch-folder', watch_folder,
                '--use-cache'
            ]
            
            if use_nanobot:
                cmd.append('--use-nanobot')
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            self.processes['invoice_watcher'] = process
            self.logger.info(f"✅ Invoice Watcher iniciado (PID: {process.pid})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando Invoice Watcher: {e}")
            return False
    
    def start_monitor(self):
        """Iniciar monitor de colas"""
        try:
            cmd = ['python', 'monitor_queues.py', '--watch']
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            self.processes['monitor'] = process
            self.logger.info(f"✅ Monitor iniciado (PID: {process.pid})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando Monitor: {e}")
            return False
    
    def check_processes(self):
        """Verificar estado de los procesos"""
        active_processes = []
        
        for name, process in self.processes.items():
            if process.poll() is None:
                active_processes.append(name)
            else:
                self.logger.warning(f"⚠️ Proceso {name} no está activo")
        
        return active_processes
    
    def stop_all_processes(self):
        """Detener todos los procesos"""
        self.logger.info("🛑 Deteniendo todos los procesos...")
        
        for name, process in self.processes.items():
            try:
                if process.poll() is None:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    process.wait(timeout=10)
                    self.logger.info(f"✅ Proceso {name} detenido")
                else:
                    self.logger.info(f"ℹ️ Proceso {name} ya estaba detenido")
            except Exception as e:
                self.logger.error(f"❌ Error deteniendo proceso {name}: {e}")
        
        self.processes.clear()
    
    def start_system(self, watch_folder: str, use_nanobot: bool = False, 
                    concurrency: int = 4, flower_port: int = 5555):
        """Iniciar el sistema completo"""
        self.logger.info("🚀 Iniciando sistema completo de facturas...")
        
        # Verificar Redis
        if not self.start_redis():
            self.logger.error("❌ No se puede continuar sin Redis")
            return False
        
        # Iniciar componentes
        components = [
            ('Celery Worker', lambda: self.start_celery_worker(concurrency)),
            ('Celery Beat', self.start_celery_beat),
            ('Flower', lambda: self.start_flower(flower_port)),
            ('Invoice Watcher', lambda: self.start_invoice_watcher(watch_folder, use_nanobot)),
            ('Monitor', self.start_monitor)
        ]
        
        for name, start_func in components:
            if not start_func():
                self.logger.error(f"❌ No se pudo iniciar {name}")
                self.stop_all_processes()
                return False
        
        self.logger.info("✅ Sistema completo iniciado exitosamente")
        self.logger.info(f"📁 Monitoreando carpeta: {watch_folder}")
        self.logger.info(f"🌐 Flower disponible en: http://localhost:{flower_port}")
        
        return True
    
    def run(self, watch_folder: str, use_nanobot: bool = False, 
            concurrency: int = 4, flower_port: int = 5555):
        """Ejecutar el sistema"""
        try:
            if self.start_system(watch_folder, use_nanobot, concurrency, flower_port):
                # Mantener el sistema corriendo
                while True:
                    time.sleep(30)
                    
                    # Verificar procesos cada 30 segundos
                    active = self.check_processes()
                    if len(active) < len(self.processes):
                        self.logger.warning("⚠️ Algunos procesos no están activos")
                    
        except KeyboardInterrupt:
            self.logger.info("👋 Deteniendo sistema...")
        finally:
            self.stop_all_processes()

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema completo de facturas')
    parser.add_argument('--watch-folder', required=True, help='Carpeta a monitorear')
    parser.add_argument('--use-nanobot', action='store_true', 
                       help='Usar Nanobot para validaciones')
    parser.add_argument('--concurrency', type=int, default=4,
                       help='Número de workers concurrentes')
    parser.add_argument('--flower-port', type=int, default=5555,
                       help='Puerto para Flower')
    
    args = parser.parse_args()
    
    # Crear carpeta de monitoreo si no existe
    os.makedirs(args.watch_folder, exist_ok=True)
    
    # Iniciar sistema
    manager = InvoiceSystemManager()
    manager.run(
        watch_folder=args.watch_folder,
        use_nanobot=args.use_nanobot,
        concurrency=args.concurrency,
        flower_port=args.flower_port
    )

if __name__ == "__main__":
    main()