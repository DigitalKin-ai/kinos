import pytest
import os
from unittest.mock import patch, mock_open
from services.mission_service import MissionService

@pytest.fixture
def mission_service():
    service = MissionService()
    # Ensure test missions directory exists
    os.makedirs("missions", exist_ok=True)
    return service

def test_mission_creation(mission_service):
    """Test mission creation and validation"""
    mission = mission_service.create_mission("test_mission")
    assert mission["name"] == "test_mission"
    assert mission["status"] == "active"
    assert mission_service.mission_exists("test_mission")

def test_get_all_missions(mission_service):
    """Test retrieving all missions"""
    # Create test missions
    mission_service.create_mission("mission1")
    mission_service.create_mission("mission2")
    
    missions = mission_service.get_all_missions()
    assert len(missions) >= 2
    assert any(m["name"] == "mission1" for m in missions)
    assert any(m["name"] == "mission2" for m in missions)

def test_get_mission(mission_service):
    """Test getting specific mission"""
    created = mission_service.create_mission("test_get")
    mission = mission_service.get_mission(created["id"])
    
    assert mission is not None
    assert mission["name"] == "test_get"
    assert "files" in mission
    assert all(f in mission["files"] for f in ["demande", "specifications", "production"])

def test_update_mission(mission_service):
    """Test mission update"""
    created = mission_service.create_mission("test_update")
    updated = mission_service.update_mission(
        created["id"],
        name="updated_name",
        description="test description"
    )
    
    assert updated is not None
    assert updated["name"] == "updated_name"

def test_save_mission_file(mission_service):
    """Test saving mission file content"""
    mission = mission_service.create_mission("test_save")
    success = mission_service.save_mission_file(
        mission["id"],
        "specifications",
        "test content"
    )
    assert success == True

def test_invalid_mission(mission_service):
    """Test handling invalid mission operations"""
    assert mission_service.get_mission(999) is None
    assert mission_service.update_mission(999) is None
    assert mission_service.save_mission_file(999, "test", "content") == False

def test_duplicate_mission(mission_service):
    """Test creating duplicate mission"""
    mission_service.create_mission("duplicate")
    with pytest.raises(ValueError):
        mission_service.create_mission("duplicate")

def test_delete_mission(mission_service):
    """Test mission deletion"""
    mission = mission_service.create_mission("test_delete")
    assert mission_service.delete_mission(mission["id"]) == True
    assert mission_service.get_mission(mission["id"]) is None
