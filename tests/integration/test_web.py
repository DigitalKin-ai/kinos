import pytest
from kinos_web import KinOSWeb

def test_web_initialization(test_config):
    """Test l'initialisation de l'application web"""
    web = KinOSWeb(test_config)
    assert web.app is not None
    assert web.agent_service is not None
    assert web.mission_service is not None

def test_agent_routes(client):
    """Test les routes des agents"""
    # Test status
    response = client.get('/api/agents/status')
    assert response.status_code == 200
    
    # Test start
    response = client.post('/api/agents/start')
    assert response.status_code == 200
    assert response.json['status'] == 'started'
    
    # Test stop
    response = client.post('/api/agents/stop')
    assert response.status_code == 200
    assert response.json['status'] == 'stopped'

def test_mission_routes(client):
    """Test les routes des missions"""
    # Test création mission
    response = client.post('/api/missions', json={
        'name': 'test_mission'
    })
    assert response.status_code == 201
    mission_id = response.json['id']
    
    # Test lecture mission
    response = client.get(f'/api/missions/{mission_id}')
    assert response.status_code == 200
    
    # Test contenu mission
    response = client.get(f'/api/missions/{mission_id}/content')
    assert response.status_code == 200

def test_notification_routes(client):
    """Test les routes des notifications"""
    # Test récupération notifications
    response = client.get('/api/notifications')
    assert response.status_code == 200
    
    # Test envoi notification
    response = client.post('/api/notifications', json={
        'type': 'info',
        'message': 'test notification'
    })
    assert response.status_code == 200
