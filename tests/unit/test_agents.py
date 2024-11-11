import pytest
from agents import (
    SpecificationsAgent,
    ProductionAgent,
    ManagementAgent,
    EvaluationAgent,
    ChroniqueurAgent,
    DuplicationAgent
)

@pytest.fixture
def agent_config():
    return {
        "file_path": "tests.md",
        "mission_name": "test_mission",
        "name": "test_agent",
        "prompt": "test prompt"
    }

def test_specifications_agent(agent_config):
    """Test l'agent de spécifications"""
    agent = SpecificationsAgent(agent_config)
    assert agent.name == "test_agent"
    assert agent.prompt == "test prompt"
    assert not agent.running

def test_production_agent(agent_config):
    """Test l'agent de production"""
    agent = ProductionAgent(agent_config)
    assert agent.name == "test_agent"
    assert not agent.running

def test_agent_lifecycle(agent_config):
    """Test le cycle de vie d'un agent"""
    agent = ManagementAgent(agent_config)
    
    # Test démarrage
    agent.start()
    assert agent.running
    assert agent.last_run is None
    
    # Test arrêt
    agent.stop()
    assert not agent.running

def test_agent_error_recovery(agent_config):
    """Test la récupération après erreur"""
    agent = EvaluationAgent(agent_config)
    assert agent.recover_from_error()

def test_agent_prompt_management(agent_config):
    """Test la gestion des prompts"""
    agent = ChroniqueurAgent(agent_config)
    
    # Test sauvegarde prompt
    assert agent.save_prompt("new prompt")
    assert agent.get_prompt() == "new prompt"

def test_duplication_detection(agent_config):
    """Test la détection de duplication"""
    agent = DuplicationAgent(agent_config)
    agent.start()
    
    # Simuler du code dupliqué
    test_content = """
    def func1():
        print("hello")
        
    def func2():
        print("hello")
    """
    
    # Le contenu devrait être analysé pour duplication
    assert agent._build_prompt({"content": test_content})
