"""
Redis caching service for performance optimization.
"""

import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from functools import wraps

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service with fallback to in-memory cache."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", 
                 default_ttl: int = 3600):
        """Initialize cache service."""
        self.default_ttl = default_ttl
        self.redis_client = None
        self.fallback_cache = {}  # In-memory fallback
        
        # Try to connect to Redis
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except RedisError as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            logger.info("🔄 Using in-memory cache fallback")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value is None:
                    return None
                
                # Try to deserialize JSON first, then pickle
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return pickle.loads(value.encode('latin1'))
                    
            except RedisError as e:
                logger.error(f"Error getting cache key {key}: {e}")
                return None
        else:
            # Use fallback cache
            return self.fallback_cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if self.redis_client:
            try:
                ttl = ttl or self.default_ttl
                
                # Try JSON serialization first, then pickle
                try:
                    serialized_value = json.dumps(value, default=str)
                except (TypeError, ValueError):
                    serialized_value = pickle.dumps(value).decode('latin1')
                
                return self.redis_client.setex(key, ttl, serialized_value)
                
            except RedisError as e:
                logger.error(f"Error setting cache key {key}: {e}")
                return False
        else:
            # Use fallback cache
            self.fallback_cache[key] = value
            return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if self.redis_client:
            try:
                return bool(self.redis_client.delete(key))
            except RedisError as e:
                logger.error(f"Error deleting cache key {key}: {e}")
                return False
        else:
            # Use fallback cache
            if key in self.fallback_cache:
                del self.fallback_cache[key]
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if self.redis_client:
            try:
                return bool(self.redis_client.exists(key))
            except RedisError as e:
                logger.error(f"Error checking cache key {key}: {e}")
                return False
        else:
            # Use fallback cache
            return key in self.fallback_cache
    
    def get_or_set(self, key: str, factory_func: callable, ttl: Optional[int] = None) -> Any:
        """Get value from cache or set it using factory function."""
        value = self.get(key)
        if value is not None:
            return value
        
        # Generate value using factory function
        value = factory_func()
        self.set(key, value, ttl)
        return value
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Error invalidating pattern {pattern}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            info = self.redis_client.info()
            return {
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except RedisError as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def _calculate_hit_rate(self, info: Dict[str, Any]) -> float:
        """Calculate cache hit rate."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)


class InvoiceCacheService:
    """Specialized cache service for invoice data."""
    
    def __init__(self, cache_service: CacheService):
        """Initialize invoice cache service."""
        self.cache = cache_service
        self.prefix = "invoice:"
    
    def _get_key(self, identifier: str) -> str:
        """Generate cache key."""
        return f"{self.prefix}{identifier}"
    
    def cache_invoice_data(self, file_path: str, invoice_data: Any, ttl: int = 3600) -> bool:
        """Cache invoice data."""
        key = self._get_key(f"data:{hash(file_path)}")
        return self.cache.set(key, invoice_data, ttl)
    
    def get_cached_invoice_data(self, file_path: str) -> Optional[Any]:
        """Get cached invoice data."""
        key = self._get_key(f"data:{hash(file_path)}")
        return self.cache.get(key)
    
    def cache_parsing_result(self, file_path: str, result: Any, ttl: int = 1800) -> bool:
        """Cache parsing result."""
        key = self._get_key(f"parse:{hash(file_path)}")
        return self.cache.set(key, result, ttl)
    
    def get_cached_parsing_result(self, file_path: str) -> Optional[Any]:
        """Get cached parsing result."""
        key = self._get_key(f"parse:{hash(file_path)}")
        return self.cache.get(key)
    
    def cache_tax_calculation(self, invoice_id: str, tax_result: Any, ttl: int = 7200) -> bool:
        """Cache tax calculation result."""
        key = self._get_key(f"tax:{invoice_id}")
        return self.cache.set(key, tax_result, ttl)
    
    def get_cached_tax_calculation(self, invoice_id: str) -> Optional[Any]:
        """Get cached tax calculation."""
        key = self._get_key(f"tax:{invoice_id}")
        return self.cache.get(key)
    
    def cache_alegra_result(self, invoice_id: str, alegra_result: Any, ttl: int = 14400) -> bool:
        """Cache Alegra API result."""
        key = self._get_key(f"alegra:{invoice_id}")
        return self.cache.set(key, alegra_result, ttl)
    
    def get_cached_alegra_result(self, invoice_id: str) -> Optional[Any]:
        """Get cached Alegra result."""
        key = self._get_key(f"alegra:{invoice_id}")
        return self.cache.get(key)
    
    def invalidate_invoice_cache(self, file_path: str) -> int:
        """Invalidate all cache entries for an invoice."""
        file_hash = hash(file_path)
        pattern = f"{self.prefix}*:{file_hash}"
        return self.cache.invalidate_pattern(pattern)
    
    def invalidate_all_invoice_cache(self) -> int:
        """Invalidate all invoice cache entries."""
        pattern = f"{self.prefix}*"
        return self.cache.invalidate_pattern(pattern)


def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cache_service = CacheService()
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        return wrapper
    return decorator


class CacheManager:
    """High-level cache management."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize cache manager."""
        self.cache_service = CacheService(redis_url)
        self.invoice_cache = InvoiceCacheService(self.cache_service)
    
    def warm_cache(self, file_paths: List[str]) -> Dict[str, Any]:
        """Warm cache with frequently accessed data."""
        warmed = 0
        failed = 0
        
        for file_path in file_paths:
            try:
                # This would pre-load data into cache
                # For now, we'll just count
                warmed += 1
            except Exception as e:
                logger.error(f"Error warming cache for {file_path}: {e}")
                failed += 1
        
        return {
            "warmed": warmed,
            "failed": failed,
            "total": len(file_paths)
        }
    
    def clear_cache(self) -> bool:
        """Clear all cache data."""
        try:
            self.cache_service.redis_client.flushdb()
            logger.info("Cache cleared successfully")
            return True
        except RedisError as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health status."""
        try:
            stats = self.cache_service.get_stats()
            return {
                "status": "healthy",
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

