#!/usr/bin/env python3
"""
Configuración de Celery para procesamiento asíncrono de facturas
"""

import os
from celery import Celery
from kombu import Queue

# Configuración de Celery
app = Celery('invoicebot')

# Configuración de broker (Redis)
app.conf.broker_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
app.conf.result_backend = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Configuración de tareas
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'
app.conf.timezone = 'America/Bogota'
app.conf.enable_utc = True

# Configuración de colas
app.conf.task_routes = {
    'invoicebot.tasks.process_invoice': {'queue': 'invoice_processing'},
    'invoicebot.tasks.generate_report': {'queue': 'report_generation'},
    'invoicebot.tasks.validate_taxes': {'queue': 'tax_validation'},
    'invoicebot.tasks.sync_alegra_data': {'queue': 'alegra_sync'},
}

# Configuración de colas personalizadas
app.conf.task_default_queue = 'default'
app.conf.task_queues = (
    Queue('default', routing_key='default'),
    Queue('invoice_processing', routing_key='invoice_processing'),
    Queue('report_generation', routing_key='report_generation'),
    Queue('tax_validation', routing_key='tax_validation'),
    Queue('alegra_sync', routing_key='alegra_sync'),
)

# Configuración de concurrencia
app.conf.worker_concurrency = int(os.getenv('CELERY_WORKER_CONCURRENCY', '4'))
app.conf.worker_prefetch_multiplier = 1
app.conf.task_acks_late = True
app.conf.worker_disable_rate_limits = False

# Configuración de retry
app.conf.task_default_retry_delay = 60
app.conf.task_max_retries = 3
app.conf.task_retry_jitter = True

# Configuración de monitoreo
app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True

# Configuración de timeouts
app.conf.task_soft_time_limit = 300  # 5 minutos
app.conf.task_time_limit = 600  # 10 minutos

# Configuración de rate limiting
app.conf.task_annotations = {
    'invoicebot.tasks.process_invoice': {'rate_limit': '10/m'},
    'invoicebot.tasks.generate_report': {'rate_limit': '5/m'},
    'invoicebot.tasks.validate_taxes': {'rate_limit': '20/m'},
    'invoicebot.tasks.sync_alegra_data': {'rate_limit': '30/m'},
}

# Auto-discovery de tareas
app.autodiscover_tasks(['invoicebot'])