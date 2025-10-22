#!/usr/bin/env python3
"""
ConfigManager centralizado con validación de schema y secrets desde env vars
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass
import jsonschema
from cryptography.fernet import Fernet

@dataclass
class ConfigSchema:
    """Schema de validación para configuración"""
    alegra: Dict[str, Any]
    nanobot: Dict[str, Any]
    logging: Dict[str, Any]
    security: Dict[str, Any]
    cache: Dict[str, Any]

class ConfigManager:
    """
    Gestor centralizado de configuración con validación de schema,
    variables de entorno con precedencia y manejo seguro de secrets
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializar ConfigManager
        
        Args:
            config_path: Ruta al archivo de configuración JSON
        """
        self.config_path = config_path or self._find_config_file()
        self._config: Dict[str, Any] = {}
        self._encryption_key: Optional[bytes] = None
        
        # Cargar configuración
        self._load_config()
        self._load_environment_overrides()
        self._validate_config()
    
    def _find_config_file(self) -> str:
        """Buscar archivo de configuración en ubicaciones estándar"""
        possible_paths = [
            'config/settings.json',
            'config.json',
            'settings.json'
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return path
        
        # Crear configuración por defecto si no existe
        default_config = self._get_default_config()
        os.makedirs('config', exist_ok=True)
        with open('config/settings.json', 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        return 'config/settings.json'
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto"""
        return {
            "version": "2.0.0",
            "alegra": {
                "base_url": "https://api.alegra.com/api/v1",
                "timeout": 30,
                "max_retries": 3,
                "rate_limit_delay": 1
            },
            "nanobot": {
                "enabled": False,
                "host": "http://localhost:8080",
                "classifier_agent": "invoice_classifier",
                "triage_agent": "invoice_triage",
                "confidence_threshold": 0.75,
                "triage_on_api_error": True
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/invoicebot.log",
                "max_size_mb": 10,
                "backup_count": 5,
                "structured": True
            },
            "security": {
                "encrypt_credentials": True,
                "max_file_size_mb": 50,
                "allowed_extensions": [".pdf", ".jpg", ".jpeg", ".png"],
                "rate_limit_per_minute": 60,
                "audit_logging": True
            },
            "cache": {
                "enabled": True,
                "ttl_seconds": 3600,
                "max_size_mb": 100,
                "redis_url": "redis://localhost:6379/0"
            }
        }
    
    def _load_config(self) -> None:
        """Cargar configuración desde archivo JSON"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ConfigurationError(f"Error cargando configuración: {e}")
    
    def _load_environment_overrides(self) -> None:
        """Cargar overrides desde variables de entorno"""
        env_mappings = {
            'ALEGRA_USER': 'alegra.email',
            'ALEGRA_TOKEN': 'alegra.token',
            'ALEGRA_BASE_URL': 'alegra.base_url',
            'NANOBOT_ENABLED': 'nanobot.enabled',
            'NANOBOT_HOST': 'nanobot.host',
            'LOG_LEVEL': 'logging.level',
            'REDIS_URL': 'cache.redis_url'
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_value(config_path, self._convert_env_value(value))
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convertir valor de env var al tipo apropiado"""
        # Boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Number
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # String
        return value
    
    def _set_nested_value(self, path: str, value: Any) -> None:
        """Establecer valor anidado en configuración"""
        keys = path.split('.')
        current = self._config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _validate_config(self) -> None:
        """Validar configuración contra schema"""
        schema = {
            "type": "object",
            "properties": {
                "alegra": {
                    "type": "object",
                    "properties": {
                        "base_url": {"type": "string"},
                        "timeout": {"type": "number", "minimum": 1},
                        "max_retries": {"type": "number", "minimum": 0},
                        "rate_limit_delay": {"type": "number", "minimum": 0}
                    },
                    "required": ["base_url"]
                },
                "nanobot": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "host": {"type": "string"},
                        "confidence_threshold": {"type": "number", "minimum": 0, "maximum": 1}
                    }
                },
                "logging": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                        "structured": {"type": "boolean"}
                    }
                }
            },
            "required": ["alegra"]
        }
        
        try:
            jsonschema.validate(self._config, schema)
        except jsonschema.ValidationError as e:
            raise ConfigurationError(f"Configuración inválida: {e.message}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtener valor de configuración con notación de puntos
        
        Args:
            key: Clave de configuración (ej: 'alegra.timeout')
            default: Valor por defecto si no existe
            
        Returns:
            Valor de configuración
        """
        keys = key.split('.')
        current = self._config
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default
    
    def get_secret(self, key: str, default: Any = None) -> Any:
        """
        Obtener secret encriptado de configuración
        
        Args:
            key: Clave del secret
            default: Valor por defecto
            
        Returns:
            Secret desencriptado
        """
        encrypted_value = self.get(key)
        if encrypted_value is None:
            return default
        
        if not self.get('security.encrypt_credentials', False):
            return encrypted_value
        
        try:
            if not self._encryption_key:
                self._encryption_key = self._get_or_create_encryption_key()
            
            fernet = Fernet(self._encryption_key)
            return fernet.decrypt(encrypted_value.encode()).decode()
        except Exception:
            # Si falla la desencriptación, devolver valor tal como está
            return encrypted_value
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Obtener o crear clave de encriptación"""
        key_file = Path('config/.encryption_key')
        
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # Solo lectura para owner
            return key
    
    def set(self, key: str, value: Any) -> None:
        """
        Establecer valor de configuración
        
        Args:
            key: Clave de configuración
            value: Valor a establecer
        """
        self._set_nested_value(key, value)
    
    def save(self) -> None:
        """Guardar configuración actual a archivo"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ConfigurationError(f"Error guardando configuración: {e}")
    
    def reload(self) -> None:
        """Recargar configuración desde archivo"""
        self._load_config()
        self._load_environment_overrides()
        self._validate_config()


class ConfigurationError(Exception):
    """Excepción para errores de configuración"""
    pass

