import pytest
from services.base_service import BaseService
from services.agent_service import AgentService
from services.mission_service import MissionService
from services.notification_service import NotificationService
from utils.exceptions import ValidationError, ServiceError

def test_base_service_validation():
    """Test la validation des entrées du BaseService"""
    service = BaseService(None)
    
    # Test validation réussie
    service._validate_input(param1="value1", param2="value2")
    
    # Test validation échouée
    with pytest.raises(ValidationError):
        service._validate_input(param1=None, param2="value2")

def test_agent_service_initialization(test_config):
    """Test l'initialisation du AgentService"""
    service = AgentService(None)
    assert service is not None
    assert hasattr(service, 'agents')
    assert hasattr(service, 'monitor_thread')

def test_mission_service_crud():
    """Test les opérations CRUD du MissionService"""
    service = MissionService()
    
    # Test création
    mission = service.create_mission("test_mission")
    assert mission is not None
    assert mission['name'] == "test_mission"
    
    # Test lecture
    missions = service.get_all_missions()
    assert len(missions) > 0
    
    # Test suppression
    assert service.delete_mission(mission['id'])

def test_notification_service_queue():
    """Test la queue de notifications"""
    service = NotificationService(None)
    
    # Test ajout notification
    service.handle_content_change(
        file_path="test.md",
        content="test content",
        panel_name="Test"
    )
    
    # Test récupération
    notifications = service.get_notifications()
    assert len(notifications) > 0
