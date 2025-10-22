"""
Tareas asíncronas con Celery
"""

from .celery_tasks import process_invoice_async, generate_report_async

__all__ = ['process_invoice_async', 'generate_report_async']

