"""Cache management utilities"""
import time
from typing import Dict, Any, Optional

class CacheManager:
    """Manages caching with TTL and cleanup"""
    
    def __init__(self, ttl: int = 3600):
        """Initialize cache manager"""
        self.ttl = ttl
        self.caches: Dict[str, Dict] = {}
        
    def get(self, cache_type: str, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        cache = self.caches.get(cache_type, {})
        if key in cache:
            value, timestamp = cache[key]
            if time.time() - timestamp <= self.ttl:
                return value
            del cache[key]
        return None
        
    def set(self, cache_type: str, key: str, value: Any) -> None:
        """Set cache value with timestamp"""
        if cache_type not in self.caches:
            self.caches[cache_type] = {}
        self.caches[cache_type][key] = (value, time.time())
        
    def cleanup(self, cache_type: Optional[str] = None) -> None:
        """Remove expired entries from cache(s)"""
        now = time.time()
        if cache_type:
            cache = self.caches.get(cache_type, {})
            expired = [k for k, (_, ts) in cache.items() if now - ts > self.ttl]
            for key in expired:
                del cache[key]
        else:
            for cache in self.caches.values():
                expired = [k for k, (_, ts) in cache.items() if now - ts > self.ttl]
                for key in expired:
                    del cache[key]
                    
    def clear(self, cache_type: Optional[str] = None) -> None:
        """Clear cache(s)"""
        if cache_type:
            self.caches[cache_type] = {}
        else:
            self.caches.clear()
