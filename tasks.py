#!/usr/bin/env python3
"""
Tareas asíncronas para procesamiento de facturas
"""

import os
import logging
from celery import current_task
from celery_config import app
from invoice_processor_conversational import ConversationalInvoiceProcessor
from alegra_reports import AlegraReports
from cache_manager import CacheManager

# Configurar logging
logger = logging.getLogger(__name__)

@app.task(bind=True, name='invoicebot.tasks.process_invoice')
def process_invoice(self, file_path: str, use_nanobot: bool = False):
    """
    Procesar factura de forma asíncrona
    
    Args:
        file_path: Ruta del archivo de factura
        use_nanobot: Si usar Nanobot para validaciones
    """
    try:
        logger.info(f"🔄 Iniciando procesamiento asíncrono de: {file_path}")
        
        # Actualizar estado de la tarea
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Iniciando procesamiento', 'file': file_path}
        )
        
        # Crear procesador
        processor = ConversationalInvoiceProcessor(use_nanobot=use_nanobot)
        
        # Actualizar estado
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Extrayendo datos', 'file': file_path}
        )
        
        # Procesar factura
        result = processor.process_invoice_conversational(file_path)
        
        if result:
            logger.info(f"✅ Factura procesada exitosamente: {file_path}")
            return {
                'status': 'SUCCESS',
                'file': file_path,
                'result': result,
                'message': 'Factura procesada exitosamente'
            }
        else:
            logger.error(f"❌ Error procesando factura: {file_path}")
            return {
                'status': 'FAILURE',
                'file': file_path,
                'error': 'No se pudo procesar la factura'
            }
            
    except Exception as e:
        logger.error(f"❌ Error en procesamiento asíncrono: {e}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'Error', 'file': file_path, 'error': str(e)}
        )
        raise

@app.task(bind=True, name='invoicebot.tasks.generate_report')
def generate_report(self, report_type: str, start_date: str, end_date: str, 
                   account_id: str = None):
    """
    Generar reporte de forma asíncrona
    
    Args:
        report_type: Tipo de reporte
        start_date: Fecha de inicio
        end_date: Fecha de fin
        account_id: ID de cuenta (opcional)
    """
    try:
        logger.info(f"📊 Generando reporte {report_type} de forma asíncrona")
        
        # Actualizar estado
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Iniciando generación de reporte', 'type': report_type}
        )
        
        # Crear generador de reportes
        reporter = AlegraReports()
        
        # Actualizar estado
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Consultando datos', 'type': report_type}
        )
        
        # Generar reporte según tipo
        if report_type == 'aging':
            result = reporter.generate_aging_report(start_date, end_date)
        elif report_type == 'cash_flow':
            result = reporter.generate_cash_flow_report(start_date, end_date)
        else:
            result = reporter.generate_ledger_report(
                start_date, end_date, report_type, account_id
            )
        
        if result:
            logger.info(f"✅ Reporte {report_type} generado exitosamente")
            return {
                'status': 'SUCCESS',
                'type': report_type,
                'result': result,
                'message': 'Reporte generado exitosamente'
            }
        else:
            logger.error(f"❌ Error generando reporte {report_type}")
            return {
                'status': 'FAILURE',
                'type': report_type,
                'error': 'No se pudo generar el reporte'
            }
            
    except Exception as e:
        logger.error(f"❌ Error en generación de reporte: {e}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'Error', 'type': report_type, 'error': str(e)}
        )
        raise

@app.task(bind=True, name='invoicebot.tasks.validate_taxes')
def validate_taxes(self, invoice_data: dict, country_code: str = 'CO'):
    """
    Validar impuestos de forma asíncrona
    
    Args:
        invoice_data: Datos de la factura
        country_code: Código del país para reglas fiscales
    """
    try:
        logger.info(f"💰 Validando impuestos para país: {country_code}")
        
        # Actualizar estado
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Validando impuestos', 'country': country_code}
        )
        
        # Importar validador de impuestos
        from tax_validator import TaxValidator
        
        validator = TaxValidator(country_code)
        result = validator.validate_invoice_taxes(invoice_data)
        
        logger.info(f"✅ Validación de impuestos completada")
        return {
            'status': 'SUCCESS',
            'country': country_code,
            'result': result,
            'message': 'Validación de impuestos completada'
        }
        
    except Exception as e:
        logger.error(f"❌ Error en validación de impuestos: {e}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'Error', 'country': country_code, 'error': str(e)}
        )
        raise

@app.task(bind=True, name='invoicebot.tasks.validate_dian', max_retries=3)
def validate_dian(self, invoice_data: dict, invoice_id: str, file_path: str):
    """
    Validar factura con DIAN con reintentos automáticos
    
    Args:
        invoice_data: Datos de la factura
        invoice_id: ID único de la factura
        file_path: Ruta del archivo de factura
    """
    try:
        logger.info(f"🔍 Validando con DIAN: {invoice_id}")
        
        # Actualizar estado
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Validando con DIAN', 'invoice_id': invoice_id}
        )
        
        # Importar validador DIAN y gestor de resiliencia
        from dian_validator import DIANValidator
        from dian_resilience import DIANResilienceManager, ComplianceStatus
        
        # Registrar factura para seguimiento
        resilience_manager = DIANResilienceManager()
        resilience_manager.register_invoice(invoice_id, file_path, invoice_data)
        
        # Intentar validación DIAN
        dian_validator = DIANValidator(test_mode=True)
        result = dian_validator.validate_electronic_invoice(invoice_data)
        
        if result.is_valid:
            # Validación exitosa
            resilience_manager.update_compliance_status(
                invoice_id, 
                ComplianceStatus.VALIDATED,
                dian_response=result.dian_response
            )
            
            logger.info(f"✅ Validación DIAN exitosa: {invoice_id}")
            return {
                'status': 'SUCCESS',
                'invoice_id': invoice_id,
                'cufe': result.cufe,
                'qr_code': result.qr_code,
                'message': 'Validación DIAN exitosa'
            }
        else:
            # Validación falló, programar reintento
            resilience_manager.update_compliance_status(
                invoice_id,
                ComplianceStatus.RETRY,
                error_message=f"Errores DIAN: {', '.join(result.errors)}"
            )
            
            # Programar reintento
            retry_delay = 60 * (2 ** self.request.retries)  # Exponential backoff
            raise self.retry(countdown=retry_delay)
            
    except Exception as e:
        logger.error(f"❌ Error en validación DIAN {invoice_id}: {e}")
        
        # Actualizar estado de fallo
        try:
            from dian_resilience import DIANResilienceManager, ComplianceStatus
            resilience_manager = DIANResilienceManager()
            resilience_manager.update_compliance_status(
                invoice_id,
                ComplianceStatus.RETRY,
                error_message=str(e)
            )
        except:
            pass
        
        # Reintentar si no hemos excedido el límite
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)
            logger.info(f"🔄 Reintentando validación DIAN en {retry_delay} segundos")
            raise self.retry(countdown=retry_delay)
        else:
            # Marcar como fallido después de todos los reintentos
            try:
                from dian_resilience import DIANResilienceManager, ComplianceStatus
                resilience_manager = DIANResilienceManager()
                resilience_manager.update_compliance_status(
                    invoice_id,
                    ComplianceStatus.FAILED,
                    error_message=f"Falló después de {self.max_retries} reintentos: {str(e)}"
                )
            except:
                pass
            
            # Notificar via Nanobot
            notify_dian_failure.delay(invoice_id, str(e))
            
            raise

@app.task(bind=True, name='invoicebot.tasks.notify_dian_failure')
def notify_dian_failure(self, invoice_id: str, error_message: str):
    """
    Notificar fallo de validación DIAN via Nanobot
    
    Args:
        invoice_id: ID de la factura
        error_message: Mensaje de error
    """
    try:
        logger.info(f"🚨 Notificando fallo DIAN: {invoice_id}")
        
        # Preparar notificación para Nanobot
        notification = {
            'type': 'dian_validation_failure',
            'invoice_id': invoice_id,
            'error': error_message,
            'timestamp': datetime.now().isoformat(),
            'priority': 'high',
            'requires_human_review': True
        }
        
        # En una implementación real, aquí se enviaría a Nanobot
        # Por ahora, solo loguear
        logger.warning(f"🚨 FALLO DIAN - Factura {invoice_id}: {error_message}")
        
        return {
            'status': 'SUCCESS',
            'invoice_id': invoice_id,
            'message': 'Notificación enviada'
        }
        
    except Exception as e:
        logger.error(f"❌ Error enviando notificación DIAN: {e}")
        raise

@app.task(bind=True, name='invoicebot.tasks.process_pending_retries')
def process_pending_retries(self):
    """
    Procesar facturas pendientes de reintento
    """
    try:
        logger.info("🔄 Procesando reintentos pendientes...")
        
        from dian_resilience import DIANResilienceManager, ComplianceStatus
        
        resilience_manager = DIANResilienceManager()
        pending_retries = resilience_manager.get_pending_retries()
        
        processed_count = 0
        
        for record in pending_retries:
            try:
                # Cargar datos de la factura desde backup
                backup_file = os.path.join(
                    resilience_manager.fallback_folder, 
                    f"{record.invoice_id}_backup.json"
                )
                
                if os.path.exists(backup_file):
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                    
                    invoice_data = backup_data['invoice_data']
                    
                    # Reintentar validación
                    validate_dian.delay(invoice_data, record.invoice_id, record.file_path)
                    processed_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Error procesando reintento {record.invoice_id}: {e}")
        
        logger.info(f"✅ Procesados {processed_count} reintentos")
        return {
            'status': 'SUCCESS',
            'processed_count': processed_count,
            'message': f'Procesados {processed_count} reintentos'
        }
        
    except Exception as e:
        logger.error(f"❌ Error procesando reintentos: {e}")
        raise

@app.task(bind=True, name='invoicebot.tasks.cleanup_compliance_records')
def cleanup_compliance_records(self, days_old: int = 30):
    """
    Limpiar registros de cumplimiento antiguos
    
    Args:
        days_old: Días de antigüedad para limpiar
    """
    try:
        logger.info(f"🧹 Limpiando registros de cumplimiento antiguos (>{days_old} días)")
        
        from dian_resilience import DIANResilienceManager
        
        resilience_manager = DIANResilienceManager()
        cleaned_count = resilience_manager.cleanup_old_records(days_old)
        
        logger.info(f"✅ Limpieza de cumplimiento completada: {cleaned_count} registros eliminados")
        return {
            'status': 'SUCCESS',
            'cleaned_count': cleaned_count,
            'message': f'Limpieza completada: {cleaned_count} registros eliminados'
        }
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza de cumplimiento: {e}")
        raise

@app.task(bind=True, name='invoicebot.tasks.generate_compliance_report')
def generate_compliance_report(self):
    """
    Generar reporte de cumplimiento fiscal
    """
    try:
        logger.info("📊 Generando reporte de cumplimiento fiscal...")
        
        from dian_resilience import DIANResilienceManager
        
        resilience_manager = DIANResilienceManager()
        stats = resilience_manager.get_compliance_stats()
        
        # Generar reporte detallado
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': stats,
            'recommendations': _generate_compliance_recommendations(stats)
        }
        
        # Guardar reporte
        report_file = f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join('reports', report_file)
        
        os.makedirs('reports', exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Reporte de cumplimiento generado: {report_path}")
        return {
            'status': 'SUCCESS',
            'report_path': report_path,
            'stats': stats,
            'message': 'Reporte de cumplimiento generado'
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando reporte de cumplimiento: {e}")
        raise

def _generate_compliance_recommendations(stats: dict) -> list:
    """Generar recomendaciones basadas en estadísticas de cumplimiento"""
    recommendations = []
    
    total = stats.get('total_invoices', 0)
    if total == 0:
        return recommendations
    
    failed_percentage = stats.get('failed_percentage', 0)
    retry_percentage = stats.get('retry_percentage', 0)
    pending_percentage = stats.get('pending_percentage', 0)
    
    if failed_percentage > 10:
        recommendations.append({
            'type': 'warning',
            'message': f'Alto porcentaje de fallos ({failed_percentage}%). Revisar configuración DIAN.',
            'action': 'Verificar conectividad y configuración de APIs'
        })
    
    if retry_percentage > 20:
        recommendations.append({
            'type': 'info',
            'message': f'Muchos reintentos pendientes ({retry_percentage}%). Considerar aumentar workers.',
            'action': 'Escalar workers de Celery'
        })
    
    if pending_percentage > 30:
        recommendations.append({
            'type': 'warning',
            'message': f'Alto porcentaje de facturas pendientes ({pending_percentage}%). Revisar procesamiento.',
            'action': 'Verificar estado de workers y colas'
        })
    
    if failed_percentage < 5 and retry_percentage < 10:
        recommendations.append({
            'type': 'success',
            'message': 'Excelente tasa de cumplimiento. Sistema funcionando óptimamente.',
            'action': 'Mantener configuración actual'
        })
    
    return recommendations

@app.task(bind=True, name='invoicebot.tasks.sync_alegra_data')
def sync_alegra_data(self, data_type: str = 'contacts'):
    """
    Sincronizar datos de Alegra en caché
    
    Args:
        data_type: Tipo de datos a sincronizar ('contacts', 'items', 'accounts')
    """
    try:
        logger.info(f"🔄 Sincronizando datos de Alegra: {data_type}")
        
        # Actualizar estado
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Sincronizando datos', 'type': data_type}
        )
        
        # Usar cache manager
        cache_manager = CacheManager()
        result = cache_manager.sync_alegra_data(data_type)
        
        logger.info(f"✅ Sincronización de {data_type} completada")
        return {
            'status': 'SUCCESS',
            'type': data_type,
            'result': result,
            'message': f'Sincronización de {data_type} completada'
        }
        
    except Exception as e:
        logger.error(f"❌ Error en sincronización: {e}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'Error', 'type': data_type, 'error': str(e)}
        )
        raise

@app.task(name='invoicebot.tasks.cleanup_old_files')
def cleanup_old_files(days_old: int = 30):
    """
    Limpiar archivos antiguos de forma asíncrona
    
    Args:
        days_old: Días de antigüedad para limpiar
    """
    try:
        logger.info(f"🧹 Limpiando archivos antiguos (>{days_old} días)")
        
        import os
        import time
        from datetime import datetime, timedelta
        
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        cleaned_files = []
        
        # Limpiar directorios de procesados
        directories = ['processed', 'error', 'high_amount']
        
        for directory in directories:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path):
                        if os.path.getmtime(file_path) < cutoff_time:
                            os.remove(file_path)
                            cleaned_files.append(file_path)
        
        logger.info(f"✅ Limpieza completada: {len(cleaned_files)} archivos eliminados")
        return {
            'status': 'SUCCESS',
            'cleaned_files': len(cleaned_files),
            'message': f'Limpieza completada: {len(cleaned_files)} archivos eliminados'
        }
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza: {e}")
        raise

# Tarea periódica para limpieza
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'invoicebot.tasks.cleanup_old_files',
        'schedule': crontab(hour=2, minute=0),  # Diario a las 2 AM
        'args': (30,)
    },
    'sync-alegra-contacts': {
        'task': 'invoicebot.tasks.sync_alegra_data',
        'schedule': crontab(hour=1, minute=0),  # Diario a la 1 AM
        'args': ('contacts',)
    },
    'sync-alegra-items': {
        'task': 'invoicebot.tasks.sync_alegra_data',
        'schedule': crontab(hour=1, minute=30),  # Diario a la 1:30 AM
        'args': ('items',)
    },
    'process-pending-retries': {
        'task': 'invoicebot.tasks.process_pending_retries',
        'schedule': crontab(minute='*/5'),  # Cada 5 minutos
        'args': ()
    },
    'cleanup-compliance-records': {
        'task': 'invoicebot.tasks.cleanup_compliance_records',
        'schedule': crontab(hour=3, minute=0),  # Diario a las 3 AM
        'args': (30,)
    },
    'generate-compliance-report': {
        'task': 'invoicebot.tasks.generate_compliance_report',
        'schedule': crontab(hour=8, minute=0),  # Diario a las 8 AM
        'args': ()
    },
}