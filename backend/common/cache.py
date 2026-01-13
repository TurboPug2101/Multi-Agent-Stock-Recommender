"""
Simple Caching Utility
Provides caching with 3-hour TTL for agent results.
"""

from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class Cache:
    """Simple in-memory cache with 3-hour TTL."""
    
    def __init__(self):
        """Initialize cache."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_hours = 3.0
    
    def generate_key(self, prefix: str, **kwargs) -> str:
        """
        Generate simple cache key.
        
        Example: generate_key('scouting', top_n=5) -> 'scouting_top_n_5'
        """
        key_parts = [prefix]
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}_{value}")
        return "_".join(key_parts).replace(" ", "").replace(".", "_")
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired (3 hours)."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        age = datetime.now() - entry['timestamp']
        
        if age > timedelta(hours=self.ttl_hours):
            del self._cache[key]
            return None
        
        logger.debug(f"Cache hit: {key}")
        return entry['data']
    
    def set(self, key: str, value: Any):
        """Store value in cache."""
        self._cache[key] = {
            'data': value,
            'timestamp': datetime.now()
        }
        logger.debug(f"Cache set: {key}")


# Global cache instance
_cache = Cache()


def get_cache() -> Cache:
    """Get the global cache instance."""
    return _cache
