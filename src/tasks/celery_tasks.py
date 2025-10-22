#!/usr/bin/env python3
"""
Tareas de Celery para procesamiento asíncrono
Consolida funcionalidad de tasks.py y celery_config.py
"""

import os
import time
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from pathlib import Path
from celery import Celery, Task
from celery.exceptions import Retry, MaxRetriesExceededError
from celery.utils.log import get_task_logger

from ..utils.feature_flags import is_feature_enabled, experimental_feature
from ..utils.monitoring import get_metrics_collector, get_structured_logger
from ..utils.cache import CacheManager
from ..exceptions import TaskError, ProcessingError

# Configuración de Celery
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Crear instancia de Celery
celery_app = Celery('betibot')

# Configuración de Celery
celery_app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Bogota',
    enable_utc=True,
    
    # Configuración de tareas
    task_track_started=True,
    task_time_limit=300,  # 5 minutos
    task_soft_time_limit=240,  # 4 minutos
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Configuración de reintentos
    task_default_retry_delay=60,  # 1 minuto
    task_max_retries=3,
    
    # Configuración de colas
    task_routes={
        'betibot.tasks.process_invoice': {'queue': 'invoices'},
        'betibot.tasks.generate_report': {'queue': 'reports'},
        'betibot.tasks.validate_dian': {'queue': 'validation'},
        'betibot.tasks.send_notification': {'queue': 'notifications'},
    },
    
    # Configuración de rate limiting
    task_annotations={
        'betibot.tasks.process_invoice': {'rate_limit': '10/m'},
        'betibot.tasks.generate_report': {'rate_limit': '5/m'},
        'betibot.tasks.validate_dian': {'rate_limit': '2/m'},
    }
)

# Logger de Celery
celery_logger = get_task_logger(__name__)

class BaseTask(Task):
    """
    Clase base para tareas de Celery con funcionalidades comunes
    """
    
    def on_success(self, retval, task_id, args, kwargs):
        """Callback de éxito"""
        celery_logger.info(f"Tarea {task_id} completada exitosamente")
        get_metrics_collector().increment_counter('celery_tasks_completed', {
            'task_name': self.name
        })
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Callback de fallo"""
        celery_logger.error(f"Tarea {task_id} falló: {exc}")
        get_metrics_collector().increment_counter('celery_tasks_failed', {
            'task_name': self.name,
            'error_type': type(exc).__name__
        })
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Callback de reintento"""
        celery_logger.warning(f"Tarea {task_id} reintentando: {exc}")
        get_metrics_collector().increment_counter('celery_tasks_retried', {
            'task_name': self.name
        })

@celery_app.task(bind=True, base=BaseTask, name='betibot.tasks.process_invoice')
def process_invoice(self, file_path: str, invoice_type: str = 'auto') -> Dict[str, Any]:
    """
    Procesar factura de forma asíncrona
    
    Args:
        file_path: Ruta del archivo de factura
        invoice_type: Tipo de factura ('purchase', 'sale', 'auto')
        
    Returns:
        Resultado del procesamiento
    """
    start_time = time.time()
    task_id = self.request.id
    
    logger = get_structured_logger('celery.process_invoice')
    logger.set_correlation_id(task_id)
    
    try:
        logger.info("Iniciando procesamiento de factura", extra={
            'file_path': file_path,
            'invoice_type': invoice_type,
            'task_id': task_id
        })
        
        # Verificar que el archivo existe
        if not Path(file_path).exists():
            raise ProcessingError(f"Archivo no encontrado: {file_path}")
        
        # Actualizar progreso
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Iniciando procesamiento...'}
        )
        
        # Importar procesador principal
        from ..core.invoice_processor import InvoiceProcessor
        
        # Inicializar procesador
        processor = InvoiceProcessor()
        
        # Procesar factura
        result = processor.process_invoice(file_path, invoice_type)
        
        # Calcular tiempo de procesamiento
        processing_time = time.time() - start_time
        
        # Registrar métricas
        get_metrics_collector().record_invoice_processed(
            invoice_type=result.get('type', 'unknown'),
            status='success'
        )
        get_metrics_collector().record_processing_time(
            process_type='invoice_processing',
            duration=processing_time,
            status='success'
        )
        
        logger.info("Factura procesada exitosamente", extra={
            'processing_time': processing_time,
            'result': result
        })
        
        return {
            'success': True,
            'task_id': task_id,
            'processing_time': processing_time,
            'result': result
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        
        # Registrar error
        get_metrics_collector().record_error(
            module='celery.process_invoice',
            error_type=type(e).__name__
        )
        get_metrics_collector().record_processing_time(
            process_type='invoice_processing',
            duration=processing_time,
            status='error'
        )
        
        logger.error("Error procesando factura", extra={
            'error': str(e),
            'processing_time': processing_time
        })
        
        # Reintentar si es posible
        if isinstance(e, (ProcessingError, TaskError)):
            raise self.retry(exc=e, countdown=60, max_retries=3)
        
        return {
            'success': False,
            'task_id': task_id,
            'error': str(e),
            'processing_time': processing_time
        }

@celery_app.task(bind=True, base=BaseTask, name='betibot.tasks.generate_report')
def generate_report(self, report_type: str, start_date: str, end_date: str, **kwargs) -> Dict[str, Any]:
    """
    Generar reporte de forma asíncrona
    
    Args:
        report_type: Tipo de reporte
        start_date: Fecha de inicio
        end_date: Fecha de fin
        **kwargs: Parámetros adicionales
        
    Returns:
        Resultado del reporte
    """
    start_time = time.time()
    task_id = self.request.id
    
    logger = get_structured_logger('celery.generate_report')
    logger.set_correlation_id(task_id)
    
    try:
        logger.info("Iniciando generación de reporte", extra={
            'report_type': report_type,
            'start_date': start_date,
            'end_date': end_date,
            'task_id': task_id
        })
        
        # Actualizar progreso
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Iniciando generación...'}
        )
        
        # Importar generador de reportes
        from ..integrations.alegra.reports import AlegraReports
        from ..integrations.alegra.client import AlegraClient
        
        # Inicializar cliente Alegra
        alegra_client = AlegraClient(
            email=os.getenv('ALEGRA_EMAIL'),
            token=os.getenv('ALEGRA_TOKEN')
        )
        
        # Inicializar generador de reportes
        reports_generator = AlegraReports(alegra_client)
        
        # Generar reporte según tipo
        if report_type == 'general_ledger':
            result = reports_generator.generate_general_ledger(
                start_date, end_date, **kwargs
            )
        elif report_type == 'trial_balance':
            result = reports_generator.generate_trial_balance(
                start_date, end_date, **kwargs
            )
        elif report_type == 'journal':
            result = reports_generator.generate_journal(
                start_date, end_date, **kwargs
            )
        elif report_type == 'auxiliary_ledgers':
            result = reports_generator.generate_auxiliary_ledgers(
                start_date, end_date, **kwargs
            )
        elif report_type == 'all':
            result = reports_generator.generate_all_reports(
                start_date, end_date, **kwargs
            )
        else:
            raise ValueError(f"Tipo de reporte no soportado: {report_type}")
        
        # Calcular tiempo de generación
        generation_time = time.time() - start_time
        
        # Registrar métricas
        get_metrics_collector().record_processing_time(
            process_type='report_generation',
            duration=generation_time,
            status='success'
        )
        
        logger.info("Reporte generado exitosamente", extra={
            'generation_time': generation_time,
            'report_type': report_type
        })
        
        return {
            'success': True,
            'task_id': task_id,
            'generation_time': generation_time,
            'result': result
        }
        
    except Exception as e:
        generation_time = time.time() - start_time
        
        # Registrar error
        get_metrics_collector().record_error(
            module='celery.generate_report',
            error_type=type(e).__name__
        )
        get_metrics_collector().record_processing_time(
            process_type='report_generation',
            duration=generation_time,
            status='error'
        )
        
        logger.error("Error generando reporte", extra={
            'error': str(e),
            'generation_time': generation_time
        })
        
        return {
            'success': False,
            'task_id': task_id,
            'error': str(e),
            'generation_time': generation_time
        }

@celery_app.task(bind=True, base=BaseTask, name='betibot.tasks.validate_dian')
@experimental_feature('dian_validation')
def validate_dian(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validar factura con DIAN de forma asíncrona
    
    Args:
        invoice_data: Datos de la factura
        
    Returns:
        Resultado de la validación
    """
    start_time = time.time()
    task_id = self.request.id
    
    logger = get_structured_logger('celery.validate_dian')
    logger.set_correlation_id(task_id)
    
    try:
        logger.info("Iniciando validación DIAN", extra={
            'invoice_data': invoice_data,
            'task_id': task_id
        })
        
        # Actualizar progreso
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Iniciando validación...'}
        )
        
        # Importar validador DIAN
        from ..integrations.dian.validator import DIANValidator
        
        # Inicializar validador
        validator = DIANValidator()
        
        # Validar factura
        result = validator.validate_invoice(invoice_data)
        
        # Calcular tiempo de validación
        validation_time = time.time() - start_time
        
        # Registrar métricas
        get_metrics_collector().record_processing_time(
            process_type='dian_validation',
            duration=validation_time,
            status='success'
        )
        
        logger.info("Validación DIAN completada", extra={
            'validation_time': validation_time,
            'result': result
        })
        
        return {
            'success': True,
            'task_id': task_id,
            'validation_time': validation_time,
            'result': result
        }
        
    except Exception as e:
        validation_time = time.time() - start_time
        
        # Registrar error
        get_metrics_collector().record_error(
            module='celery.validate_dian',
            error_type=type(e).__name__
        )
        get_metrics_collector().record_processing_time(
            process_type='dian_validation',
            duration=validation_time,
            status='error'
        )
        
        logger.error("Error validando con DIAN", extra={
            'error': str(e),
            'validation_time': validation_time
        })
        
        return {
            'success': False,
            'task_id': task_id,
            'error': str(e),
            'validation_time': validation_time
        }

@celery_app.task(bind=True, base=BaseTask, name='betibot.tasks.send_notification')
def send_notification(self, notification_type: str, recipient: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enviar notificación de forma asíncrona
    
    Args:
        notification_type: Tipo de notificación
        recipient: Destinatario
        data: Datos de la notificación
        
    Returns:
        Resultado del envío
    """
    start_time = time.time()
    task_id = self.request.id
    
    logger = get_structured_logger('celery.send_notification')
    logger.set_correlation_id(task_id)
    
    try:
        logger.info("Enviando notificación", extra={
            'notification_type': notification_type,
            'recipient': recipient,
            'task_id': task_id
        })
        
        # Actualizar progreso
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Enviando notificación...'}
        )
        
        # Simular envío de notificación
        # En una implementación real, aquí se integraría con servicios de notificación
        time.sleep(1)  # Simular tiempo de envío
        
        # Calcular tiempo de envío
        send_time = time.time() - start_time
        
        # Registrar métricas
        get_metrics_collector().record_processing_time(
            process_type='notification_sending',
            duration=send_time,
            status='success'
        )
        
        logger.info("Notificación enviada exitosamente", extra={
            'send_time': send_time,
            'notification_type': notification_type
        })
        
        return {
            'success': True,
            'task_id': task_id,
            'send_time': send_time,
            'notification_type': notification_type
        }
        
    except Exception as e:
        send_time = time.time() - start_time
        
        # Registrar error
        get_metrics_collector().record_error(
            module='celery.send_notification',
            error_type=type(e).__name__
        )
        get_metrics_collector().record_processing_time(
            process_type='notification_sending',
            duration=send_time,
            status='error'
        )
        
        logger.error("Error enviando notificación", extra={
            'error': str(e),
            'send_time': send_time
        })
        
        return {
            'success': False,
            'task_id': task_id,
            'error': str(e),
            'send_time': send_time
        }

@celery_app.task(bind=True, base=BaseTask, name='betibot.tasks.cleanup_old_files')
def cleanup_old_files(self, days_old: int = 30) -> Dict[str, Any]:
    """
    Limpiar archivos antiguos de forma asíncrona
    
    Args:
        days_old: Días de antigüedad para limpiar
        
    Returns:
        Resultado de la limpieza
    """
    start_time = time.time()
    task_id = self.request.id
    
    logger = get_structured_logger('celery.cleanup_old_files')
    logger.set_correlation_id(task_id)
    
    try:
        logger.info("Iniciando limpieza de archivos antiguos", extra={
            'days_old': days_old,
            'task_id': task_id
        })
        
        # Actualizar progreso
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Iniciando limpieza...'}
        )
        
        # Directorios a limpiar
        cleanup_dirs = [
            'facturas/processed',
            'facturas/error',
            'reports',
            'logs'
        ]
        
        cleaned_files = 0
        total_size = 0
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        for dir_path in cleanup_dirs:
            if Path(dir_path).exists():
                for file_path in Path(dir_path).rglob('*'):
                    if file_path.is_file():
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime < cutoff_date:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            cleaned_files += 1
                            total_size += file_size
        
        # Calcular tiempo de limpieza
        cleanup_time = time.time() - start_time
        
        # Registrar métricas
        get_metrics_collector().record_processing_time(
            process_type='file_cleanup',
            duration=cleanup_time,
            status='success'
        )
        
        logger.info("Limpieza completada", extra={
            'cleanup_time': cleanup_time,
            'cleaned_files': cleaned_files,
            'total_size': total_size
        })
        
        return {
            'success': True,
            'task_id': task_id,
            'cleanup_time': cleanup_time,
            'cleaned_files': cleaned_files,
            'total_size': total_size
        }
        
    except Exception as e:
        cleanup_time = time.time() - start_time
        
        # Registrar error
        get_metrics_collector().record_error(
            module='celery.cleanup_old_files',
            error_type=type(e).__name__
        )
        get_metrics_collector().record_processing_time(
            process_type='file_cleanup',
            duration=cleanup_time,
            status='error'
        )
        
        logger.error("Error en limpieza de archivos", extra={
            'error': str(e),
            'cleanup_time': cleanup_time
        })
        
        return {
            'success': False,
            'task_id': task_id,
            'error': str(e),
            'cleanup_time': cleanup_time
        }

# Funciones de utilidad para el manejo de tareas
def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Obtener estado de una tarea
    
    Args:
        task_id: ID de la tarea
        
    Returns:
        Estado de la tarea
    """
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            'task_id': task_id,
            'status': result.status,
            'result': result.result,
            'info': result.info
        }
    except Exception as e:
        return {
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(e)
        }

def cancel_task(task_id: str) -> bool:
    """
    Cancelar una tarea
    
    Args:
        task_id: ID de la tarea
        
    Returns:
        True si se canceló correctamente
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        return True
    except Exception:
        return False

def get_active_tasks() -> List[Dict[str, Any]]:
    """
    Obtener tareas activas
    
    Returns:
        Lista de tareas activas
    """
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        tasks = []
        for worker, worker_tasks in active_tasks.items():
            for task in worker_tasks:
                tasks.append({
                    'worker': worker,
                    'task_id': task['id'],
                    'name': task['name'],
                    'args': task['args'],
                    'kwargs': task['kwargs']
                })
        
        return tasks
    except Exception:
        return []

def get_queue_stats() -> Dict[str, Any]:
    """
    Obtener estadísticas de colas
    
    Returns:
        Estadísticas de colas
    """
    try:
        inspect = celery_app.control.inspect()
        
        return {
            'active': inspect.active(),
            'scheduled': inspect.scheduled(),
            'reserved': inspect.reserved(),
            'stats': inspect.stats()
        }
    except Exception as e:
        return {'error': str(e)}