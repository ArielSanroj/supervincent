#!/usr/bin/env python3
"""
Sistema de logging estructurado con JSON y correlation IDs
"""

import json
import logging
import time
import uuid
from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime

class StructuredLogger:
    """
    Logger estructurado que genera logs en formato JSON
    con correlation IDs y metadatos enriquecidos
    """
    
    def __init__(self, name: str, level: str = 'INFO'):
        self.name = name
        self.logger = logging.getLogger(name)
        self.correlation_id: Optional[str] = None
        
        # Configurar handler si no existe
        if not self.logger.handlers:
            self._setup_handlers()
        
        # Establecer nivel
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    def _setup_handlers(self) -> None:
        """Configurar handlers para logging estructurado"""
        # Handler para archivo JSON
        log_file = Path('logs/invoicebot.json')
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(StructuredFormatter())
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def set_correlation_id(self, correlation_id: Optional[str] = None) -> None:
        """Establecer correlation ID para tracking de requests"""
        self.correlation_id = correlation_id or str(uuid.uuid4())
    
    def _create_log_record(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Crear registro de log estructurado"""
        record = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level.upper(),
            'logger': self.name,
            'message': message,
            'correlation_id': self.correlation_id,
            'process_id': str(uuid.uuid4())[:8]
        }
        
        if extra:
            record.update(extra)
        
        return record
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log nivel DEBUG"""
        record = self._create_log_record('DEBUG', message, extra)
        self.logger.debug(json.dumps(record, ensure_ascii=False))
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log nivel INFO"""
        record = self._create_log_record('INFO', message, extra)
        self.logger.info(json.dumps(record, ensure_ascii=False))
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log nivel WARNING"""
        record = self._create_log_record('WARNING', message, extra)
        self.logger.warning(json.dumps(record, ensure_ascii=False))
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log nivel ERROR"""
        record = self._create_log_record('ERROR', message, extra)
        self.logger.error(json.dumps(record, ensure_ascii=False))
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log nivel CRITICAL"""
        record = self._create_log_record('CRITICAL', message, extra)
        self.logger.critical(json.dumps(record, ensure_ascii=False))
    
    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """Log específico para métricas de performance"""
        extra = {
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            'performance_metric': True,
            **kwargs
        }
        self.info(f"Performance: {operation}", extra=extra)
    
    def log_api_call(self, method: str, url: str, status_code: int, duration: float, **kwargs) -> None:
        """Log específico para llamadas a API"""
        extra = {
            'api_method': method,
            'api_url': url,
            'api_status_code': status_code,
            'api_duration_ms': round(duration * 1000, 2),
            'api_call': True,
            **kwargs
        }
        
        level = 'info' if 200 <= status_code < 400 else 'warning' if 400 <= status_code < 500 else 'error'
        getattr(self, level)(f"API call: {method} {url}", extra=extra)
    
    def log_security_event(self, event_type: str, **kwargs) -> None:
        """Log específico para eventos de seguridad"""
        extra = {
            'security_event': True,
            'security_event_type': event_type,
            **kwargs
        }
        self.warning(f"Security event: {event_type}", extra=extra)

class StructuredFormatter(logging.Formatter):
    """Formatter que mantiene el formato JSON de los logs estructurados"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Si el mensaje ya es JSON, devolverlo tal como está
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except (json.JSONDecodeError, TypeError):
            # Si no es JSON, crear formato estructurado básico
            return json.dumps({
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }, ensure_ascii=False)

