import pytest
import time
from kinos_web import KinOSWeb

def test_agent_startup_time(test_config):
    """Test le temps de démarrage des agents"""
    web = KinOSWeb(test_config)
    
    start_time = time.time()
    web.agent_service.start_all_agents()
    startup_time = time.time() - start_time
    
    assert startup_time < 2.0  # Démarrage < 2 secondes
    
    web.agent_service.stop_all_agents()

def test_file_operations_performance():
    """Test les performances des opérations fichiers"""
    from services.mission_service import MissionService
    service = MissionService()
    
    # Test création rapide
    start_time = time.time()
    mission = service.create_mission("perf_test")
    creation_time = time.time() - start_time
    assert creation_time < 0.1  # Création < 100ms
    
    # Test lecture rapide
    start_time = time.time()
    missions = service.get_all_missions()
    read_time = time.time() - start_time
    assert read_time < 0.05  # Lecture < 50ms

def test_notification_throughput():
    """Test le débit des notifications"""
    from services.notification_service import NotificationService
    service = NotificationService(None)
    
    # Test envoi batch notifications
    start_time = time.time()
    for i in range(100):
        service.handle_content_change(
            file_path=f"test_{i}.md",
            content=f"content_{i}",
            panel_name="Test"
        )
    processing_time = time.time() - start_time
    
    # 100 notifications en moins de 1 seconde
    assert processing_time < 1.0

def test_cache_performance():
    """Test les performances du cache"""
    from services.cache_service import CacheService
    service = CacheService(None)
    
    # Test set/get rapide
    start_time = time.time()
    for i in range(1000):
        service.set(f"key_{i}", f"value_{i}")
        value = service.get(f"key_{i}")
        assert value == f"value_{i}"
    
    cache_time = time.time() - start_time
    # 1000 opérations en moins de 1 seconde
    assert cache_time < 1.0
