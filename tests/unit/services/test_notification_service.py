import pytest
from unittest.mock import Mock
from services.notification_service import NotificationService
from utils.exceptions import ServiceError

class MockWebInstance:
    def __init__(self):
        self.logger = Mock()
        self.file_paths = {
            'test.md': 'test/test.md'
        }
        self.file_manager = Mock()

@pytest.fixture
def notification_service():
    return NotificationService(MockWebInstance())

def test_notification_queue(notification_service):
    """Test notification queue operations"""
    notification_service.handle_content_change("test.md", "content", "Test")
    notifications = notification_service.get_notifications()
    assert len(notifications) == 1
    assert notifications[0]["panel"] == "Test"
    assert notifications[0]["content"] == "content"

def test_content_cache(notification_service):
    """Test content caching"""
    notification_service.handle_content_change("test.md", "content1", "Test")
    assert "test.md" in notification_service.content_cache
    assert notification_service.content_cache["test.md"] == "content1"
    
    # Update content
    notification_service.handle_content_change("test.md", "content2", "Test")
    assert notification_service.content_cache["test.md"] == "content2"

def test_cache_metrics(notification_service):
    """Test cache performance metrics"""
    notification_service.handle_content_change("test.md", "content", "Test")
    notification_service.get_notifications()
    
    assert notification_service.cache_hits >= 0
    assert notification_service.cache_misses >= 0
    assert notification_service.total_notifications == 1

def test_cleanup(notification_service):
    """Test cleanup operation"""
    notification_service.handle_content_change("test.md", "content", "Test")
    notification_service.cleanup()
    
    assert len(notification_service.notifications_queue) == 0
    assert len(notification_service.content_cache) == 0
    assert len(notification_service.last_modified) == 0

def test_invalid_input(notification_service):
    """Test handling of invalid input"""
    with pytest.raises(ServiceError):
        notification_service.handle_content_change(None, None, None)
