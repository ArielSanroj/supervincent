#!/usr/bin/env python3
"""
Sistema de caché LRU/Redis para optimización de performance
"""

import json
import time
import hashlib
import logging
from typing import Any, Optional, Dict, Union, Callable
from functools import wraps
from collections import OrderedDict
import redis
from redis.exceptions import RedisError

from ..exceptions import CacheError

class LRUCache:
    """
    Implementación de caché LRU en memoria
    """
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        Inicializar caché LRU
        
        Args:
            max_size: Tamaño máximo del caché
            ttl: Tiempo de vida en segundos
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}
        self.logger = logging.getLogger(__name__)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtener valor del caché
        
        Args:
            key: Clave del caché
            
        Returns:
            Valor o None si no existe o expiró
        """
        if key not in self.cache:
            return None
        
        # Verificar expiración
        if time.time() - self.timestamps[key] > self.ttl:
            self._remove(key)
            return None
        
        # Mover al final (más reciente)
        value = self.cache.pop(key)
        self.cache[key] = value
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Establecer valor en el caché
        
        Args:
            key: Clave del caché
            value: Valor a almacenar
        """
        # Si ya existe, remover primero
        if key in self.cache:
            self._remove(key)
        
        # Si está lleno, remover el menos reciente
        if len(self.cache) >= self.max_size:
            self._remove_oldest()
        
        # Agregar nuevo valor
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def delete(self, key: str) -> bool:
        """
        Eliminar valor del caché
        
        Args:
            key: Clave del caché
            
        Returns:
            True si existía, False si no
        """
        if key in self.cache:
            self._remove(key)
            return True
        return False
    
    def clear(self) -> None:
        """Limpiar todo el caché"""
        self.cache.clear()
        self.timestamps.clear()
    
    def _remove(self, key: str) -> None:
        """Remover clave del caché"""
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
    
    def _remove_oldest(self) -> None:
        """Remover el elemento más antiguo"""
        if self.cache:
            oldest_key = next(iter(self.cache))
            self._remove(oldest_key)
    
    def size(self) -> int:
        """Obtener tamaño actual del caché"""
        return len(self.cache)
    
    def stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del caché"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'ttl': self.ttl,
            'keys': list(self.cache.keys())
        }

class RedisCache:
    """
    Cliente de caché Redis con fallback a LRU
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ttl: int = 3600,
        fallback_to_lru: bool = True
    ):
        """
        Inicializar caché Redis
        
        Args:
            host: Host de Redis
            port: Puerto de Redis
            db: Base de datos de Redis
            password: Contraseña de Redis
            ttl: Tiempo de vida por defecto
            fallback_to_lru: Usar LRU como fallback si Redis falla
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.ttl = ttl
        self.fallback_to_lru = fallback_to_lru
        
        self.logger = logging.getLogger(__name__)
        
        # Inicializar cliente Redis
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Probar conexión
            self.redis_client.ping()
            self.redis_available = True
            self.logger.info("Conexión a Redis establecida")
            
        except RedisError as e:
            self.logger.warning("No se pudo conectar a Redis", extra={"error": str(e)})
            self.redis_available = False
            self.redis_client = None
        
        # Fallback LRU
        if not self.redis_available and fallback_to_lru:
            self.lru_cache = LRUCache(max_size=1000, ttl=ttl)
            self.logger.info("Usando caché LRU como fallback")
        else:
            self.lru_cache = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtener valor del caché
        
        Args:
            key: Clave del caché
            
        Returns:
            Valor o None si no existe
        """
        try:
            if self.redis_available:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
                return None
            elif self.lru_cache:
                return self.lru_cache.get(key)
            else:
                return None
                
        except Exception as e:
            self.logger.error("Error obteniendo del caché", extra={"key": key, "error": str(e)})
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Establecer valor en el caché
        
        Args:
            key: Clave del caché
            value: Valor a almacenar
            ttl: Tiempo de vida en segundos
            
        Returns:
            True si se almacenó correctamente
        """
        try:
            ttl = ttl or self.ttl
            
            if self.redis_available:
                serialized_value = json.dumps(value, default=str)
                return self.redis_client.setex(key, ttl, serialized_value)
            elif self.lru_cache:
                self.lru_cache.set(key, value)
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error("Error estableciendo en caché", extra={"key": key, "error": str(e)})
            return False
    
    def delete(self, key: str) -> bool:
        """
        Eliminar valor del caché
        
        Args:
            key: Clave del caché
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            if self.redis_available:
                return bool(self.redis_client.delete(key))
            elif self.lru_cache:
                return self.lru_cache.delete(key)
            else:
                return False
                
        except Exception as e:
            self.logger.error("Error eliminando del caché", extra={"key": key, "error": str(e)})
            return False
    
    def clear(self) -> bool:
        """
        Limpiar todo el caché
        
        Returns:
            True si se limpió correctamente
        """
        try:
            if self.redis_available:
                self.redis_client.flushdb()
                return True
            elif self.lru_cache:
                self.lru_cache.clear()
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error("Error limpiando caché", extra={"error": str(e)})
            return False
    
    def exists(self, key: str) -> bool:
        """
        Verificar si una clave existe
        
        Args:
            key: Clave del caché
            
        Returns:
            True si existe
        """
        try:
            if self.redis_available:
                return bool(self.redis_client.exists(key))
            elif self.lru_cache:
                return key in self.lru_cache.cache
            else:
                return False
                
        except Exception as e:
            self.logger.error("Error verificando existencia en caché", extra={"key": key, "error": str(e)})
            return False
    
    def get_ttl(self, key: str) -> int:
        """
        Obtener TTL de una clave
        
        Args:
            key: Clave del caché
            
        Returns:
            TTL en segundos o -1 si no existe
        """
        try:
            if self.redis_available:
                return self.redis_client.ttl(key)
            else:
                return -1
                
        except Exception as e:
            self.logger.error("Error obteniendo TTL", extra={"key": key, "error": str(e)})
            return -1
    
    def stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del caché
        
        Returns:
            Estadísticas del caché
        """
        try:
            if self.redis_available:
                info = self.redis_client.info()
                return {
                    'type': 'redis',
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': info.get('used_memory_human', '0B'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0)
                }
            elif self.lru_cache:
                return {
                    'type': 'lru',
                    **self.lru_cache.stats()
                }
            else:
                return {'type': 'none', 'available': False}
                
        except Exception as e:
            self.logger.error("Error obteniendo estadísticas", extra={"error": str(e)})
            return {'type': 'error', 'error': str(e)}

def cache_key(*args, **kwargs) -> str:
    """
    Generar clave de caché a partir de argumentos
    
    Args:
        *args: Argumentos posicionales
        **kwargs: Argumentos con nombre
        
    Returns:
        Clave de caché generada
    """
    # Crear string único a partir de argumentos
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()

def cached(
    cache_instance: Union[LRUCache, RedisCache],
    ttl: int = 3600,
    key_prefix: str = "",
    key_func: Optional[Callable] = None
):
    """
    Decorador para caché de funciones
    
    Args:
        cache_instance: Instancia del caché
        ttl: Tiempo de vida en segundos
        key_prefix: Prefijo para las claves
        key_func: Función personalizada para generar claves
        
    Returns:
        Decorador
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave
            if key_func:
                cache_key_str = key_func(*args, **kwargs)
            else:
                cache_key_str = cache_key(*args, **kwargs)
            
            full_key = f"{key_prefix}:{cache_key_str}" if key_prefix else cache_key_str
            
            # Intentar obtener del caché
            cached_result = cache_instance.get(full_key)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y almacenar resultado
            result = func(*args, **kwargs)
            cache_instance.set(full_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

class CacheManager:
    """
    Gestor centralizado de caché para la aplicación
    """
    
    def __init__(
        self,
        redis_host: str = 'localhost',
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None
    ):
        """
        Inicializar gestor de caché
        
        Args:
            redis_host: Host de Redis
            redis_port: Puerto de Redis
            redis_db: Base de datos de Redis
            redis_password: Contraseña de Redis
        """
        self.logger = logging.getLogger(__name__)
        
        # Caché principal (Redis con fallback LRU)
        self.main_cache = RedisCache(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            ttl=3600,
            fallback_to_lru=True
        )
        
        # Caché específico para OCR (TTL más largo)
        self.ocr_cache = RedisCache(
            host=redis_host,
            port=redis_port,
            db=redis_db + 1,  # Diferente DB
            password=redis_password,
            ttl=86400,  # 24 horas
            fallback_to_lru=True
        )
        
        # Caché específico para contactos/items Alegra
        self.alegra_cache = RedisCache(
            host=redis_host,
            port=redis_port,
            db=redis_db + 2,  # Diferente DB
            password=redis_password,
            ttl=1800,  # 30 minutos
            fallback_to_lru=True
        )
        
        self.logger.info("CacheManager inicializado")
    
    def get_ocr_result(self, image_hash: str) -> Optional[Any]:
        """Obtener resultado de OCR del caché"""
        return self.ocr_cache.get(f"ocr:{image_hash}")
    
    def set_ocr_result(self, image_hash: str, result: Any) -> bool:
        """Almacenar resultado de OCR en caché"""
        return self.ocr_cache.set(f"ocr:{image_hash}", result)
    
    def get_contact_id(self, name: str, contact_type: str) -> Optional[str]:
        """Obtener ID de contacto del caché"""
        key = f"contact:{contact_type}:{name.lower()}"
        return self.alegra_cache.get(key)
    
    def set_contact_id(self, name: str, contact_type: str, contact_id: str) -> bool:
        """Almacenar ID de contacto en caché"""
        key = f"contact:{contact_type}:{name.lower()}"
        return self.alegra_cache.set(key, contact_id)
    
    def get_item_id(self, name: str, price: float) -> Optional[str]:
        """Obtener ID de item del caché"""
        key = f"item:{name.lower()}:{price}"
        return self.alegra_cache.get(key)
    
    def set_item_id(self, name: str, price: float, item_id: str) -> bool:
        """Almacenar ID de item en caché"""
        key = f"item:{name.lower()}:{price}"
        return self.alegra_cache.set(key, item_id)
    
    def get_accounting_account(self, account_code: str) -> Optional[Dict[str, Any]]:
        """Obtener cuenta contable del caché"""
        return self.alegra_cache.get(f"account:{account_code}")
    
    def set_accounting_account(self, account_code: str, account_data: Dict[str, Any]) -> bool:
        """Almacenar cuenta contable en caché"""
        return self.alegra_cache.set(f"account:{account_code}", account_data)
    
    def clear_all_caches(self) -> bool:
        """Limpiar todos los cachés"""
        try:
            main_cleared = self.main_cache.clear()
            ocr_cleared = self.ocr_cache.clear()
            alegra_cleared = self.alegra_cache.clear()
            
            return main_cleared and ocr_cleared and alegra_cleared
            
        except Exception as e:
            self.logger.error("Error limpiando cachés", extra={"error": str(e)})
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de todos los cachés"""
        return {
            'main_cache': self.main_cache.stats(),
            'ocr_cache': self.ocr_cache.stats(),
            'alegra_cache': self.alegra_cache.stats()
        }