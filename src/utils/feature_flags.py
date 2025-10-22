#!/usr/bin/env python3
"""
Sistema de feature flags para integraciones experimentales
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

class FeatureStatus(Enum):
    """Estados de las features"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    EXPERIMENTAL = "experimental"
    BETA = "beta"
    DEPRECATED = "deprecated"

@dataclass
class FeatureConfig:
    """Configuración de una feature"""
    name: str
    status: FeatureStatus
    description: str
    enabled_by_default: bool = False
    experimental: bool = False
    beta: bool = False
    deprecated: bool = False
    config: Optional[Dict[str, Any]] = None

class FeatureFlags:
    """
    Gestor de feature flags para controlar funcionalidades experimentales
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializar gestor de feature flags
        
        Args:
            config_file: Archivo de configuración de features
        """
        self.logger = logging.getLogger(__name__)
        
        # Configuración por defecto
        self.default_features = {
            'nanobot_integration': FeatureConfig(
                name='nanobot_integration',
                status=FeatureStatus.EXPERIMENTAL,
                description='Integración con Nanobot para clasificación inteligente',
                enabled_by_default=False,
                experimental=True
            ),
            'dian_validation': FeatureConfig(
                name='dian_validation',
                status=FeatureStatus.BETA,
                description='Validación de facturas electrónicas con DIAN',
                enabled_by_default=False,
                beta=True
            ),
            'superbincent_integration': FeatureConfig(
                name='superbincent_integration',
                status=FeatureStatus.EXPERIMENTAL,
                description='Integración con SuperBincent para procesamiento avanzado',
                enabled_by_default=False,
                experimental=True
            ),
            'advanced_ocr': FeatureConfig(
                name='advanced_ocr',
                status=FeatureStatus.ENABLED,
                description='OCR avanzado con preprocesamiento de imágenes',
                enabled_by_default=True,
                experimental=False
            ),
            'tax_calculation': FeatureConfig(
                name='tax_calculation',
                status=FeatureStatus.ENABLED,
                description='Cálculo automático de impuestos colombianos',
                enabled_by_default=True,
                experimental=False
            ),
            'alegra_reports': FeatureConfig(
                name='alegra_reports',
                status=FeatureStatus.ENABLED,
                description='Generación de reportes contables desde Alegra',
                enabled_by_default=True,
                experimental=False
            ),
            'celery_async': FeatureConfig(
                name='celery_async',
                status=FeatureStatus.BETA,
                description='Procesamiento asíncrono con Celery',
                enabled_by_default=False,
                beta=True
            ),
            'redis_cache': FeatureConfig(
                name='redis_cache',
                status=FeatureStatus.BETA,
                description='Caché Redis para optimización de performance',
                enabled_by_default=False,
                beta=True
            ),
            'prometheus_metrics': FeatureConfig(
                name='prometheus_metrics',
                status=FeatureStatus.EXPERIMENTAL,
                description='Métricas de Prometheus para monitoring',
                enabled_by_default=False,
                experimental=True
            ),
            'health_checks': FeatureConfig(
                name='health_checks',
                status=FeatureStatus.ENABLED,
                description='Health checks para monitoreo de servicios',
                enabled_by_default=True,
                experimental=False
            )
        }
        
        # Cargar configuración
        self.features = self.default_features.copy()
        self.config_file = config_file or "config/feature_flags.json"
        self._load_config()
        
        self.logger.info("FeatureFlags inicializado", extra={
            "total_features": len(self.features),
            "experimental_features": len([f for f in self.features.values() if f.experimental]),
            "beta_features": len([f for f in self.features.values() if f.beta])
        })
    
    def _load_config(self) -> None:
        """Cargar configuración desde archivo"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Actualizar configuración
                for feature_name, feature_data in config_data.get('features', {}).items():
                    if feature_name in self.features:
                        # Actualizar estado si está en la configuración
                        if 'status' in feature_data:
                            try:
                                self.features[feature_name].status = FeatureStatus(feature_data['status'])
                            except ValueError:
                                self.logger.warning(f"Estado inválido para feature {feature_name}")
                        
                        # Actualizar configuración adicional
                        if 'config' in feature_data:
                            self.features[feature_name].config = feature_data['config']
                
                self.logger.info("Configuración de features cargada", extra={"file": self.config_file})
            else:
                self.logger.info("Archivo de configuración no encontrado, usando valores por defecto")
                
        except Exception as e:
            self.logger.error("Error cargando configuración de features", extra={"error": str(e)})
    
    def _save_config(self) -> None:
        """Guardar configuración a archivo"""
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = {
                'features': {
                    name: {
                        'status': feature.status.value,
                        'description': feature.description,
                        'experimental': feature.experimental,
                        'beta': feature.beta,
                        'deprecated': feature.deprecated,
                        'config': feature.config
                    }
                    for name, feature in self.features.items()
                }
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Configuración de features guardada", extra={"file": self.config_file})
            
        except Exception as e:
            self.logger.error("Error guardando configuración de features", extra={"error": str(e)})
    
    def is_enabled(self, feature_name: str) -> bool:
        """
        Verificar si una feature está habilitada
        
        Args:
            feature_name: Nombre de la feature
            
        Returns:
            True si está habilitada
        """
        # Verificar variable de entorno primero
        env_var = f"FEATURE_{feature_name.upper()}"
        env_value = os.getenv(env_var)
        
        if env_value is not None:
            return env_value.lower() in ('true', '1', 'yes', 'on')
        
        # Verificar configuración
        if feature_name not in self.features:
            self.logger.warning(f"Feature {feature_name} no encontrada")
            return False
        
        feature = self.features[feature_name]
        
        # Verificar si está deprecada
        if feature.deprecated:
            self.logger.warning(f"Feature {feature_name} está deprecada")
            return False
        
        # Verificar estado
        return feature.status in [FeatureStatus.ENABLED, FeatureStatus.EXPERIMENTAL, FeatureStatus.BETA]
    
    def is_experimental(self, feature_name: str) -> bool:
        """
        Verificar si una feature es experimental
        
        Args:
            feature_name: Nombre de la feature
            
        Returns:
            True si es experimental
        """
        if feature_name not in self.features:
            return False
        
        return self.features[feature_name].experimental
    
    def is_beta(self, feature_name: str) -> bool:
        """
        Verificar si una feature está en beta
        
        Args:
            feature_name: Nombre de la feature
            
        Returns:
            True si está en beta
        """
        if feature_name not in self.features:
            return False
        
        return self.features[feature_name].beta
    
    def is_deprecated(self, feature_name: str) -> bool:
        """
        Verificar si una feature está deprecada
        
        Args:
            feature_name: Nombre de la feature
            
        Returns:
            True si está deprecada
        """
        if feature_name not in self.features:
            return False
        
        return self.features[feature_name].deprecated
    
    def enable_feature(self, feature_name: str) -> bool:
        """
        Habilitar una feature
        
        Args:
            feature_name: Nombre de la feature
            
        Returns:
            True si se habilitó correctamente
        """
        if feature_name not in self.features:
            self.logger.error(f"Feature {feature_name} no encontrada")
            return False
        
        self.features[feature_name].status = FeatureStatus.ENABLED
        self._save_config()
        
        self.logger.info(f"Feature {feature_name} habilitada")
        return True
    
    def disable_feature(self, feature_name: str) -> bool:
        """
        Deshabilitar una feature
        
        Args:
            feature_name: Nombre de la feature
            
        Returns:
            True si se deshabilitó correctamente
        """
        if feature_name not in self.features:
            self.logger.error(f"Feature {feature_name} no encontrada")
            return False
        
        self.features[feature_name].status = FeatureStatus.DISABLED
        self._save_config()
        
        self.logger.info(f"Feature {feature_name} deshabilitada")
        return True
    
    def set_feature_status(self, feature_name: str, status: FeatureStatus) -> bool:
        """
        Establecer estado de una feature
        
        Args:
            feature_name: Nombre de la feature
            status: Nuevo estado
            
        Returns:
            True si se estableció correctamente
        """
        if feature_name not in self.features:
            self.logger.error(f"Feature {feature_name} no encontrada")
            return False
        
        self.features[feature_name].status = status
        self._save_config()
        
        self.logger.info(f"Feature {feature_name} establecida como {status.value}")
        return True
    
    def get_feature_config(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtener configuración de una feature
        
        Args:
            feature_name: Nombre de la feature
            
        Returns:
            Configuración de la feature o None
        """
        if feature_name not in self.features:
            return None
        
        return self.features[feature_name].config or {}
    
    def set_feature_config(self, feature_name: str, config: Dict[str, Any]) -> bool:
        """
        Establecer configuración de una feature
        
        Args:
            feature_name: Nombre de la feature
            config: Configuración a establecer
            
        Returns:
            True si se estableció correctamente
        """
        if feature_name not in self.features:
            self.logger.error(f"Feature {feature_name} no encontrada")
            return False
        
        self.features[feature_name].config = config
        self._save_config()
        
        self.logger.info(f"Configuración de feature {feature_name} actualizada")
        return True
    
    def get_all_features(self) -> Dict[str, FeatureConfig]:
        """
        Obtener todas las features
        
        Returns:
            Diccionario con todas las features
        """
        return self.features.copy()
    
    def get_enabled_features(self) -> Dict[str, FeatureConfig]:
        """
        Obtener features habilitadas
        
        Returns:
            Diccionario con features habilitadas
        """
        return {
            name: feature for name, feature in self.features.items()
            if self.is_enabled(name)
        }
    
    def get_experimental_features(self) -> Dict[str, FeatureConfig]:
        """
        Obtener features experimentales
        
        Returns:
            Diccionario con features experimentales
        """
        return {
            name: feature for name, feature in self.features.items()
            if self.is_experimental(name)
        }
    
    def get_beta_features(self) -> Dict[str, FeatureConfig]:
        """
        Obtener features en beta
        
        Returns:
            Diccionario con features en beta
        """
        return {
            name: feature for name, feature in self.features.items()
            if self.is_beta(name)
        }
    
    def get_deprecated_features(self) -> Dict[str, FeatureConfig]:
        """
        Obtener features deprecadas
        
        Returns:
            Diccionario con features deprecadas
        """
        return {
            name: feature for name, feature in self.features.items()
            if self.is_deprecated(name)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de features
        
        Returns:
            Estadísticas de features
        """
        total_features = len(self.features)
        enabled_features = len(self.get_enabled_features())
        experimental_features = len(self.get_experimental_features())
        beta_features = len(self.get_beta_features())
        deprecated_features = len(self.get_deprecated_features())
        
        return {
            'total_features': total_features,
            'enabled_features': enabled_features,
            'experimental_features': experimental_features,
            'beta_features': beta_features,
            'deprecated_features': deprecated_features,
            'enabled_percentage': (enabled_features / total_features * 100) if total_features > 0 else 0
        }

# Instancia global de feature flags
feature_flags = FeatureFlags()

def is_feature_enabled(feature_name: str) -> bool:
    """
    Función de conveniencia para verificar si una feature está habilitada
    
    Args:
        feature_name: Nombre de la feature
        
    Returns:
        True si está habilitada
    """
    return feature_flags.is_enabled(feature_name)

def require_feature(feature_name: str):
    """
    Decorador para requerir que una feature esté habilitada
    
    Args:
        feature_name: Nombre de la feature requerida
        
    Returns:
        Decorador
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not feature_flags.is_enabled(feature_name):
                raise RuntimeError(f"Feature {feature_name} no está habilitada")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def experimental_feature(feature_name: str):
    """
    Decorador para marcar funcionalidad como experimental
    
    Args:
        feature_name: Nombre de la feature experimental
        
    Returns:
        Decorador
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not feature_flags.is_enabled(feature_name):
                raise RuntimeError(f"Feature experimental {feature_name} no está habilitada")
            
            if feature_flags.is_experimental(feature_name):
                logging.getLogger(__name__).warning(
                    f"Usando feature experimental {feature_name}",
                    extra={"feature": feature_name, "function": func.__name__}
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

