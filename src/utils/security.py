#!/usr/bin/env python3
"""
Módulo de seguridad con sanitización, validación y rate limiting
"""

import re
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict, deque
from dataclasses import dataclass
import logging

from ..exceptions import SecurityError, ValidationError

@dataclass
class SecurityConfig:
    """Configuración de seguridad"""
    max_file_size_mb: int = 50
    allowed_extensions: Set[str] = None
    rate_limit_per_minute: int = 60
    audit_logging: bool = True
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}

class InputValidator:
    """
    Validador de entrada con sanitización y validación robusta
    """
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.logger = logging.getLogger(__name__)
        
        # Patrones de regex seguros
        self.safe_patterns = {
            'filename': re.compile(r'^[a-zA-Z0-9._-]+$'),
            'contact_name': re.compile(r'^[a-zA-Z0-9\s\.\-_]+$'),
            'amount': re.compile(r'^\d+(\.\d{1,2})?$'),
            'date': re.compile(r'^\d{4}-\d{2}-\d{2}$')
        }
        
        # Caracteres peligrosos
        self.dangerous_chars = {'<', '>', '"', "'", '&', ';', '(', ')', '|', '`', '$'}
    
    def validate_file_path(self, file_path: str) -> bool:
        """
        Validar ruta de archivo con whitelist de extensiones y sanitización
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            True si es válido, False en caso contrario
        """
        try:
            path = Path(file_path)
            
            # Verificar que el archivo existe
            if not path.exists():
                self.logger.warning("Archivo no encontrado", extra={"file_path": file_path})
                return False
            
            # Verificar extensión
            if path.suffix.lower() not in self.config.allowed_extensions:
                self.logger.warning("Extensión no permitida", extra={
                    "file_path": file_path,
                    "extension": path.suffix,
                    "allowed": list(self.config.allowed_extensions)
                })
                return False
            
            # Verificar tamaño
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.config.max_file_size_mb:
                self.logger.warning("Archivo demasiado grande", extra={
                    "file_path": file_path,
                    "size_mb": file_size_mb,
                    "max_size_mb": self.config.max_file_size_mb
                })
                return False
            
            # Verificar nombre de archivo seguro
            if not self.safe_patterns['filename'].match(path.name):
                self.logger.warning("Nombre de archivo contiene caracteres peligrosos", extra={
                    "file_path": file_path,
                    "filename": path.name
                })
                return False
            
            return True
            
        except Exception as e:
            self.logger.error("Error validando archivo", extra={
                "file_path": file_path,
                "error": str(e)
            })
            return False
    
    def sanitize_contact_name(self, name: str) -> str:
        """
        Sanitizar nombre de contacto eliminando caracteres peligrosos
        
        Args:
            name: Nombre original
            
        Returns:
            Nombre sanitizado
        """
        if not name:
            return "Consumidor Final"
        
        # Eliminar caracteres peligrosos
        sanitized = ''.join(c for c in name if c not in self.dangerous_chars)
        
        # Limitar longitud
        sanitized = sanitized[:100]
        
        # Validar con regex
        if not self.safe_patterns['contact_name'].match(sanitized):
            self.logger.warning("Nombre de contacto no válido, usando fallback", extra={
                "original": name,
                "sanitized": sanitized
            })
            return "Consumidor Final"
        
        return sanitized.strip()
    
    def validate_amount(self, amount: Any) -> Optional[float]:
        """
        Validar y convertir monto a float de forma segura
        
        Args:
            amount: Monto a validar
            
        Returns:
            Monto como float o None si no es válido
        """
        try:
            if isinstance(amount, (int, float)):
                amount_str = str(amount)
            else:
                amount_str = str(amount).strip()
            
            # Validar formato
            if not self.safe_patterns['amount'].match(amount_str):
                return None
            
            amount_float = float(amount_str)
            
            # Validar rango razonable
            if amount_float < 0 or amount_float > 1_000_000_000:  # 1 billón
                return None
            
            return amount_float
            
        except (ValueError, TypeError):
            return None
    
    def validate_date(self, date_str: str) -> bool:
        """
        Validar formato de fecha YYYY-MM-DD
        
        Args:
            date_str: Fecha como string
            
        Returns:
            True si es válida, False en caso contrario
        """
        if not isinstance(date_str, str):
            return False
        
        return bool(self.safe_patterns['date'].match(date_str.strip()))

class SecurityManager:
    """
    Gestor de seguridad con rate limiting y audit logging
    """
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting por IP/cliente
        self.rate_limits: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Audit log
        self.audit_events: List[Dict[str, Any]] = []
    
    def check_rate_limit(self, client_id: str) -> bool:
        """
        Verificar rate limit para un cliente
        
        Args:
            client_id: Identificador del cliente
            
        Returns:
            True si está dentro del límite, False si excede
        """
        now = time.time()
        minute_ago = now - 60
        
        # Limpiar timestamps antiguos
        client_requests = self.rate_limits[client_id]
        while client_requests and client_requests[0] < minute_ago:
            client_requests.popleft()
        
        # Verificar límite
        if len(client_requests) >= self.config.rate_limit_per_minute:
            self.log_audit_event('rate_limit_exceeded', {
                'client_id': client_id,
                'requests_count': len(client_requests)
            })
            return False
        
        # Registrar nueva request
        client_requests.append(now)
        return True
    
    def log_audit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Registrar evento de auditoría
        
        Args:
            event_type: Tipo de evento
            data: Datos del evento
        """
        if not self.config.audit_logging:
            return
        
        event = {
            'timestamp': time.time(),
            'event_type': event_type,
            'data': data
        }
        
        self.audit_events.append(event)
        
        # Mantener solo los últimos 1000 eventos
        if len(self.audit_events) > 1000:
            self.audit_events = self.audit_events[-1000:]
        
        self.logger.info("Audit event", extra=event)
    
    def get_audit_events(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtener eventos de auditoría
        
        Args:
            event_type: Filtrar por tipo de evento
            
        Returns:
            Lista de eventos
        """
        if event_type:
            return [event for event in self.audit_events if event['event_type'] == event_type]
        return self.audit_events.copy()
    
    def hash_sensitive_data(self, data: str) -> str:
        """
        Hashear datos sensibles para logging
        
        Args:
            data: Datos a hashear
            
        Returns:
            Hash de los datos
        """
        return hashlib.sha256(data.encode()).hexdigest()[:8]

