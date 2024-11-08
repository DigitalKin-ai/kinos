import pytest
from flask import json

def test_start_all_agents(client):
    """Test starting all agents"""
    response = client.post('/api/agents/start')
    assert response.status_code == 200
    assert response.json["status"] == "started"

def test_stop_all_agents(client):
    """Test stopping all agents"""
    response = client.post('/api/agents/stop')
    assert response.status_code == 200
    assert response.json["status"] == "stopped"

def test_get_agents_status(client):
    """Test getting agent status"""
    response = client.get('/api/agents/status')
    assert response.status_code == 200
    assert isinstance(response.json, dict)

def test_get_agent_prompt(client):
    """Test getting agent prompt"""
    response = client.get('/api/agent/specification/prompt')
    assert response.status_code == 200
    assert "prompt" in response.json

def test_save_agent_prompt(client):
    """Test saving agent prompt"""
    data = {"prompt": "Test prompt"}
    response = client.post(
        '/api/agent/specification/prompt',
        data=json.dumps(data),
        content_type='application/json'
    )
    assert response.status_code == 200
    assert response.json["status"] == "success"

def test_invalid_agent_prompt(client):
    """Test saving invalid agent prompt"""
    response = client.post(
        '/api/agent/specification/prompt',
        data=json.dumps({}),
        content_type='application/json'
    )
    assert response.status_code == 400

def test_control_agent(client):
    """Test agent control endpoints"""
    # Test start
    response = client.post('/api/agent/specification/start')
    assert response.status_code == 200
    
    # Test stop
    response = client.post('/api/agent/specification/stop')
    assert response.status_code == 200

def test_invalid_agent_action(client):
    """Test invalid agent action"""
    response = client.post('/api/agent/specification/invalid')
    assert response.status_code == 400
