#!/usr/bin/env python3
"""
Sistema de monitoreo con Prometheus y structured logging
"""

import time
import json
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import defaultdict, Counter

try:
    from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from ..utils.feature_flags import is_feature_enabled

class LogLevel(Enum):
    """Niveles de log"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class MetricData:
    """Datos de métrica"""
    name: str
    value: Union[int, float]
    labels: Dict[str, str]
    timestamp: datetime
    type: str

@dataclass
class LogEntry:
    """Entrada de log estructurado"""
    timestamp: datetime
    level: LogLevel
    message: str
    module: str
    function: str
    correlation_id: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

class MetricsCollector:
    """
    Recolector de métricas para Prometheus
    """
    
    def __init__(self, port: int = 8000, enabled: bool = None):
        """
        Inicializar recolector de métricas
        
        Args:
            port: Puerto para servidor de métricas
            enabled: Si está habilitado (None para auto-detectar)
        """
        self.port = port
        self.enabled = enabled if enabled is not None else is_feature_enabled('prometheus_metrics')
        self.logger = logging.getLogger(__name__)
        
        # Métricas de Prometheus
        self.metrics = {}
        self.metrics_lock = threading.Lock()
        
        # Inicializar métricas si está habilitado
        if self.enabled and PROMETHEUS_AVAILABLE:
            self._initialize_metrics()
            self._start_server()
        elif self.enabled and not PROMETHEUS_AVAILABLE:
            self.logger.warning("Prometheus no disponible, métricas deshabilitadas")
            self.enabled = False
    
    def _initialize_metrics(self) -> None:
        """Inicializar métricas de Prometheus"""
        try:
            # Contadores
            self.metrics['invoices_processed'] = PrometheusCounter(
                'betibot_invoices_processed_total',
                'Total de facturas procesadas',
                ['type', 'status']
            )
            
            self.metrics['api_requests'] = PrometheusCounter(
                'betibot_api_requests_total',
                'Total de requests a APIs externas',
                ['service', 'endpoint', 'status']
            )
            
            self.metrics['errors'] = PrometheusCounter(
                'betibot_errors_total',
                'Total de errores',
                ['module', 'error_type']
            )
            
            # Histogramas
            self.metrics['processing_time'] = Histogram(
                'betibot_processing_duration_seconds',
                'Tiempo de procesamiento',
                ['type', 'status'],
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
            )
            
            self.metrics['api_latency'] = Histogram(
                'betibot_api_latency_seconds',
                'Latencia de APIs externas',
                ['service', 'endpoint'],
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
            )
            
            # Gauges
            self.metrics['active_tasks'] = Gauge(
                'betibot_active_tasks',
                'Tareas activas',
                ['type']
            )
            
            self.metrics['cache_size'] = Gauge(
                'betibot_cache_size',
                'Tamaño del caché',
                ['cache_type']
            )
            
            self.metrics['queue_size'] = Gauge(
                'betibot_queue_size',
                'Tamaño de colas',
                ['queue_name']
            )
            
            self.logger.info("Métricas de Prometheus inicializadas")
            
        except Exception as e:
            self.logger.error("Error inicializando métricas", extra={"error": str(e)})
            self.enabled = False
    
    def _start_server(self) -> None:
        """Iniciar servidor de métricas"""
        try:
            start_http_server(self.port)
            self.logger.info(f"Servidor de métricas iniciado en puerto {self.port}")
        except Exception as e:
            self.logger.error("Error iniciando servidor de métricas", extra={"error": str(e)})
            self.enabled = False
    
    def increment_counter(self, name: str, labels: Dict[str, str] = None) -> None:
        """
        Incrementar contador
        
        Args:
            name: Nombre del contador
            labels: Etiquetas del contador
        """
        if not self.enabled:
            return
        
        try:
            with self.metrics_lock:
                if name in self.metrics:
                    self.metrics[name].labels(**(labels or {})).inc()
        except Exception as e:
            self.logger.error("Error incrementando contador", extra={"name": name, "error": str(e)})
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """
        Observar histograma
        
        Args:
            name: Nombre del histograma
            value: Valor a observar
            labels: Etiquetas del histograma
        """
        if not self.enabled:
            return
        
        try:
            with self.metrics_lock:
                if name in self.metrics:
                    self.metrics[name].labels(**(labels or {})).observe(value)
        except Exception as e:
            self.logger.error("Error observando histograma", extra={"name": name, "error": str(e)})
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """
        Establecer gauge
        
        Args:
            name: Nombre del gauge
            value: Valor a establecer
            labels: Etiquetas del gauge
        """
        if not self.enabled:
            return
        
        try:
            with self.metrics_lock:
                if name in self.metrics:
                    self.metrics[name].labels(**(labels or {})).set(value)
        except Exception as e:
            self.logger.error("Error estableciendo gauge", extra={"name": name, "error": str(e)})
    
    def record_invoice_processed(self, invoice_type: str, status: str) -> None:
        """Registrar factura procesada"""
        self.increment_counter('invoices_processed', {
            'type': invoice_type,
            'status': status
        })
    
    def record_api_request(self, service: str, endpoint: str, status: str) -> None:
        """Registrar request a API"""
        self.increment_counter('api_requests', {
            'service': service,
            'endpoint': endpoint,
            'status': status
        })
    
    def record_error(self, module: str, error_type: str) -> None:
        """Registrar error"""
        self.increment_counter('errors', {
            'module': module,
            'error_type': error_type
        })
    
    def record_processing_time(self, process_type: str, duration: float, status: str) -> None:
        """Registrar tiempo de procesamiento"""
        self.observe_histogram('processing_time', duration, {
            'type': process_type,
            'status': status
        })
    
    def record_api_latency(self, service: str, endpoint: str, latency: float) -> None:
        """Registrar latencia de API"""
        self.observe_histogram('api_latency', latency, {
            'service': service,
            'endpoint': endpoint
        })
    
    def set_active_tasks(self, task_type: str, count: int) -> None:
        """Establecer tareas activas"""
        self.set_gauge('active_tasks', count, {'type': task_type})
    
    def set_cache_size(self, cache_type: str, size: int) -> None:
        """Establecer tamaño de caché"""
        self.set_gauge('cache_size', size, {'cache_type': cache_type})
    
    def set_queue_size(self, queue_name: str, size: int) -> None:
        """Establecer tamaño de cola"""
        self.set_gauge('queue_size', size, {'queue_name': queue_name})

class StructuredLogger:
    """
    Logger estructurado con formato JSON
    """
    
    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        """
        Inicializar logger estructurado
        
        Args:
            name: Nombre del logger
            level: Nivel de log
        """
        self.name = name
        self.level = level
        self.logger = logging.getLogger(name)
        self.correlation_id = None
        self.extra_data = {}
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """Establecer ID de correlación"""
        self.correlation_id = correlation_id
    
    def set_extra_data(self, data: Dict[str, Any]) -> None:
        """Establecer datos adicionales"""
        self.extra_data.update(data)
    
    def _log(self, level: LogLevel, message: str, extra: Dict[str, Any] = None) -> None:
        """
        Log interno
        
        Args:
            level: Nivel de log
            message: Mensaje
            extra: Datos adicionales
        """
        if level.value not in [LogLevel.DEBUG.value, LogLevel.INFO.value, LogLevel.WARNING.value, LogLevel.ERROR.value, LogLevel.CRITICAL.value]:
            return
        
        # Crear entrada de log estructurada
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            module=self.name,
            function="",  # Se puede obtener del stack trace
            correlation_id=self.correlation_id,
            extra={**(extra or {}), **self.extra_data}
        )
        
        # Convertir a JSON
        log_data = asdict(log_entry)
        log_data['timestamp'] = log_entry.timestamp.isoformat()
        log_data['level'] = log_entry.level.value
        
        # Log con nivel apropiado
        if level == LogLevel.DEBUG:
            self.logger.debug(json.dumps(log_data, ensure_ascii=False))
        elif level == LogLevel.INFO:
            self.logger.info(json.dumps(log_data, ensure_ascii=False))
        elif level == LogLevel.WARNING:
            self.logger.warning(json.dumps(log_data, ensure_ascii=False))
        elif level == LogLevel.ERROR:
            self.logger.error(json.dumps(log_data, ensure_ascii=False))
        elif level == LogLevel.CRITICAL:
            self.logger.critical(json.dumps(log_data, ensure_ascii=False))
    
    def debug(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Log de debug"""
        self._log(LogLevel.DEBUG, message, extra)
    
    def info(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Log de info"""
        self._log(LogLevel.INFO, message, extra)
    
    def warning(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Log de warning"""
        self._log(LogLevel.WARNING, message, extra)
    
    def error(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Log de error"""
        self._log(LogLevel.ERROR, message, extra)
    
    def critical(self, message: str, extra: Dict[str, Any] = None) -> None:
        """Log crítico"""
        self._log(LogLevel.CRITICAL, message, extra)

class HealthChecker:
    """
    Health checker para monitoreo de servicios
    """
    
    def __init__(self, port: int = 8080, enabled: bool = None):
        """
        Inicializar health checker
        
        Args:
            port: Puerto para health check
            enabled: Si está habilitado (None para auto-detectar)
        """
        self.port = port
        self.enabled = enabled if enabled is not None else is_feature_enabled('health_checks')
        self.logger = logging.getLogger(__name__)
        
        # Estado de servicios
        self.services_status = {}
        self.last_check = {}
        
        # Inicializar health check si está habilitado
        if self.enabled:
            self._initialize_health_check()
    
    def _initialize_health_check(self) -> None:
        """Inicializar health check"""
        try:
            # Aquí se podría implementar un servidor HTTP simple
            # Para ahora, solo registramos que está habilitado
            self.logger.info(f"Health checker habilitado en puerto {self.port}")
        except Exception as e:
            self.logger.error("Error inicializando health check", extra={"error": str(e)})
            self.enabled = False
    
    def check_service(self, service_name: str, check_func: callable) -> Dict[str, Any]:
        """
        Verificar estado de un servicio
        
        Args:
            service_name: Nombre del servicio
            check_func: Función de verificación
            
        Returns:
            Estado del servicio
        """
        try:
            start_time = time.time()
            result = check_func()
            duration = time.time() - start_time
            
            status = {
                'service': service_name,
                'status': 'healthy' if result else 'unhealthy',
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            }
            
            self.services_status[service_name] = status
            self.last_check[service_name] = datetime.now()
            
            return status
            
        except Exception as e:
            status = {
                'service': service_name,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            self.services_status[service_name] = status
            self.last_check[service_name] = datetime.now()
            
            return status
    
    def get_overall_status(self) -> Dict[str, Any]:
        """
        Obtener estado general del sistema
        
        Returns:
            Estado general
        """
        if not self.services_status:
            return {
                'status': 'unknown',
                'message': 'No hay servicios registrados',
                'timestamp': datetime.now().isoformat()
            }
        
        healthy_services = sum(1 for s in self.services_status.values() if s['status'] == 'healthy')
        total_services = len(self.services_status)
        
        overall_status = 'healthy' if healthy_services == total_services else 'degraded'
        if healthy_services == 0:
            overall_status = 'unhealthy'
        
        return {
            'status': overall_status,
            'healthy_services': healthy_services,
            'total_services': total_services,
            'services': self.services_status,
            'timestamp': datetime.now().isoformat()
        }

# Instancias globales
metrics_collector = MetricsCollector()
structured_logger = StructuredLogger('betibot')
health_checker = HealthChecker()

def get_metrics_collector() -> MetricsCollector:
    """Obtener instancia del recolector de métricas"""
    return metrics_collector

def get_structured_logger(name: str = 'betibot') -> StructuredLogger:
    """Obtener instancia del logger estructurado"""
    return StructuredLogger(name)

def get_health_checker() -> HealthChecker:
    """Obtener instancia del health checker"""
    return health_checker

