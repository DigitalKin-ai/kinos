"""
CacheService - Multi-level caching system for KinOS
"""
from typing import Any, Optional, Dict
import os
import time
from collections import OrderedDict
from threading import Lock
from utils.exceptions import ServiceError
from services.base_service import BaseService
from utils.path_manager import PathManager

class CacheService(BaseService):
    """
    Multi-level caching service with:
    - Memory cache (LRU)
    - File content cache
    - Prompt cache
    - Metadata cache
    """
    
    def __init__(self, web_instance, config: Dict = None):
        super().__init__(web_instance)
        self.config = config or {}
        
        # Use PathManager for cache directory
        self.cache_dir = PathManager.get_temp_path()
        
        # Cache settings
        self.max_size = self.config.get('CACHE_SIZE', 1000)
        self.ttl = self.config.get('CACHE_TTL', 3600)  # 1 hour default
        self.cleanup_interval = self.config.get('CLEANUP_INTERVAL', 300)  # 5 min
        
        # Initialize caches with paths
        self._memory_cache: OrderedDict = OrderedDict()
        self._file_cache: Dict = {}
        self._prompt_cache: Dict = {}
        self._metadata_cache: Dict = {}
        
        # Cache metrics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        # Thread safety
        self._lock = Lock()
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Start cleanup timer
        self._start_cleanup_timer()
        
    def get(self, key: str, cache_type: str = 'memory') -> Optional[Any]:
        """Get value from specified cache"""
        try:
            with self._lock:
                cache = self._get_cache(cache_type)
                if key not in cache:
                    self.misses += 1
                    return None
                    
                value, timestamp = cache[key]
                if self._is_expired(timestamp):
                    self._remove(key, cache_type)
                    self.misses += 1
                    return None
                    
                self.hits += 1
                if cache_type == 'memory':
                    self._memory_cache.move_to_end(key)
                return value
                
        except Exception as e:
            self.logger.log(f"Cache get error: {str(e)}", level='error')
            return None
            
    def set(self, key: str, value: Any, cache_type: str = 'memory') -> bool:
        """Set value in specified cache"""
        try:
            with self._lock:
                cache = self._get_cache(cache_type)
                
                # Enforce size limit for memory cache
                if cache_type == 'memory' and len(self._memory_cache) >= self.max_size:
                    self._evict()
                    
                cache[key] = (value, time.time())
                
                if cache_type == 'memory':
                    self._memory_cache.move_to_end(key)
                return True
                
        except Exception as e:
            self.logger.log(f"Cache set error: {str(e)}", level='error')
            return False
            
    def invalidate(self, key: str, cache_type: str = 'memory') -> bool:
        """Remove key from specified cache"""
        try:
            with self._lock:
                return self._remove(key, cache_type)
        except Exception as e:
            self.logger.log(f"Cache invalidate error: {str(e)}", level='error')
            return False
            
    def clear(self, cache_type: Optional[str] = None) -> bool:
        """Clear specified or all caches"""
        try:
            with self._lock:
                if cache_type:
                    cache = self._get_cache(cache_type)
                    cache.clear()
                else:
                    self._memory_cache.clear()
                    self._file_cache.clear()
                    self._prompt_cache.clear()
                    self._metadata_cache.clear()
                return True
        except Exception as e:
            self.logger.log(f"Cache clear error: {str(e)}", level='error')
            return False
            
    def get_metrics(self) -> Dict:
        """Get cache performance metrics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate': hit_rate,
            'memory_size': len(self._memory_cache),
            'file_cache_size': len(self._file_cache),
            'prompt_cache_size': len(self._prompt_cache),
            'metadata_cache_size': len(self._metadata_cache)
        }
        
    def _get_cache(self, cache_type: str) -> Dict:
        """Get cache dictionary by type"""
        if cache_type == 'memory':
            return self._memory_cache
        elif cache_type == 'file':
            return self._file_cache
        elif cache_type == 'prompt':
            return self._prompt_cache
        elif cache_type == 'metadata':
            return self._metadata_cache
        else:
            raise ValueError(f"Invalid cache type: {cache_type}")
            
    def _get_cache_file_path(self, key: str) -> str:
        """Get full path for a cache file"""
        return PathManager.get_temp_file(prefix=f"cache_{key}_", suffix=".tmp")
            
    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired"""
        return time.time() - timestamp > self.ttl
        
    def _evict(self) -> None:
        """Evict oldest entry from memory cache"""
        if self._memory_cache:
            self._memory_cache.popitem(last=False)
            self.evictions += 1
            
    def _remove(self, key: str, cache_type: str) -> bool:
        """Remove key from specified cache"""
        cache = self._get_cache(cache_type)
        if key in cache:
            del cache[key]
            return True
        return False
        
    def _start_cleanup_timer(self) -> None:
        """Start periodic cache cleanup"""
        import threading
        
        def cleanup():
            while True:
                try:
                    time.sleep(self.cleanup_interval)
                    self._cleanup_expired()
                except Exception as e:
                    self.logger.log(f"Cache cleanup error: {str(e)}", level='error')
                    
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
        
    def _cleanup_expired(self) -> None:
        """Remove all expired entries from all caches"""
        with self._lock:
            for cache_type in ['memory', 'file', 'prompt', 'metadata']:
                cache = self._get_cache(cache_type)
                expired = [
                    key for key, (_, timestamp) in cache.items()
                    if self._is_expired(timestamp)
                ]
                for key in expired:
                    self._remove(key, cache_type)
