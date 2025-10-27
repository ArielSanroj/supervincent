"""
Base repository classes and interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository."""
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities with pagination."""
        pass
    
    @abstractmethod
    def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[T]:
        """Update entity."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete entity."""
        pass
    
    @abstractmethod
    def search(self, query: Dict[str, Any], limit: int = 100) -> List[T]:
        """Search entities."""
        pass


class CacheRepository(BaseRepository[T]):
    """Repository with caching support."""
    
    def __init__(self, cache_ttl: int = 3600):
        """Initialize cache repository."""
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
    
    def _get_cache_key(self, entity_id: str) -> str:
        """Generate cache key."""
        return f"{self.__class__.__name__}:{entity_id}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is valid."""
        if cache_key not in self._cache_timestamps:
            return False
        
        age = (datetime.now() - self._cache_timestamps[cache_key]).total_seconds()
        return age < self.cache_ttl
    
    def _get_from_cache(self, entity_id: str) -> Optional[T]:
        """Get entity from cache."""
        cache_key = self._get_cache_key(entity_id)
        
        if cache_key in self._cache and self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        return None
    
    def _set_cache(self, entity_id: str, entity: T) -> None:
        """Set entity in cache."""
        cache_key = self._get_cache_key(entity_id)
        self._cache[cache_key] = entity
        self._cache_timestamps[cache_key] = datetime.now()
    
    def _invalidate_cache(self, entity_id: str) -> None:
        """Invalidate cache entry."""
        cache_key = self._get_cache_key(entity_id)
        self._cache.pop(cache_key, None)
        self._cache_timestamps.pop(cache_key, None)
    
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID with caching."""
        # Try cache first
        cached_entity = self._get_from_cache(entity_id)
        if cached_entity is not None:
            return cached_entity
        
        # Fetch from storage
        entity = self._fetch_by_id(entity_id)
        if entity is not None:
            self._set_cache(entity_id, entity)
        
        return entity
    
    @abstractmethod
    def _fetch_by_id(self, entity_id: str) -> Optional[T]:
        """Fetch entity from storage (implemented by subclasses)."""
        pass

