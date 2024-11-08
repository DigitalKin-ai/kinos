import pytest
import time
from services.cache_service import CacheService

def test_cache_set_get():
    """Test basic cache set/get operations"""
    cache = CacheService(None)
    cache.set("key", "value")
    assert cache.get("key") == "value"

def test_cache_invalidation():
    """Test cache invalidation"""
    cache = CacheService(None)
    cache.set("key", "value")
    cache.invalidate("key")
    assert cache.get("key") is None

def test_cache_metrics():
    """Test cache metrics collection"""
    cache = CacheService(None)
    cache.set("key", "value")
    cache.get("key")  # Hit
    cache.get("missing")  # Miss
    
    metrics = cache.get_metrics()
    assert metrics["hits"] == 1
    assert metrics["misses"] == 1
    assert metrics["evictions"] == 0

def test_cache_eviction():
    """Test cache eviction with size limit"""
    cache = CacheService({"CACHE_SIZE": 2})
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")  # Should evict key1
    
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"

def test_cache_ttl():
    """Test cache TTL expiration"""
    cache = CacheService({"CACHE_TTL": 0.1})  # 100ms TTL
    cache.set("key", "value")
    assert cache.get("key") == "value"
    
    time.sleep(0.2)  # Wait for expiration
    assert cache.get("key") is None

def test_cache_clear():
    """Test cache clear operation"""
    cache = CacheService(None)
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    
    cache.clear()
    assert cache.get("key1") is None
    assert cache.get("key2") is None
