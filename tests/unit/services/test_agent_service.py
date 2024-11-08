import pytest
from unittest.mock import Mock, patch
from services.agent_service import AgentService
from utils.exceptions import ServiceError

class MockWebInstance:
    def __init__(self):
        self.log_message = Mock()
        self.mission_service = Mock()
        self.mission_service.get_all_missions.return_value = [{'name': 'test_mission'}]

@pytest.fixture
def agent_service():
    return AgentService(MockWebInstance())

def test_agent_initialization(agent_service):
    """Test agent initialization with config"""
    config = {
        "anthropic_api_key": "test_key",
        "openai_api_key": "test_key"
    }
    agent_service.init_agents(config)
    assert len(agent_service.agents) > 0
    assert "Specification" in agent_service.agents
    assert "Production" in agent_service.agents

def test_agent_lifecycle(agent_service):
    """Test agent start/stop cycle"""
    config = {
        "anthropic_api_key": "test_key",
        "openai_api_key": "test_key"
    }
    agent_service.init_agents(config)
    
    agent_service.start_all_agents()
    assert agent_service.running == True
    
    agent_service.stop_all_agents()
    assert agent_service.running == False

def test_get_agent_status(agent_service):
    """Test getting agent status"""
    config = {
        "anthropic_api_key": "test_key",
        "openai_api_key": "test_key"
    }
    agent_service.init_agents(config)
    
    status = agent_service.get_agent_status()
    assert isinstance(status, dict)
    assert "specification" in status
    assert "running" in status["specification"]

def test_invalid_config():
    """Test initialization with invalid config"""
    service = AgentService(MockWebInstance())
    with pytest.raises(ValueError):
        service.init_agents({})

def test_monitor_thread(agent_service):
    """Test monitor thread management"""
    config = {
        "anthropic_api_key": "test_key",
        "openai_api_key": "test_key"
    }
    agent_service.init_agents(config)
    
    # Start should create monitor thread
    agent_service.start_all_agents()
    assert agent_service.monitor_thread is not None
    assert agent_service.monitor_thread.is_alive()
    
    # Stop should terminate monitor thread
    agent_service.stop_all_agents()
    assert not agent_service.monitor_thread.is_alive()
