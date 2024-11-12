"""Services package initialization"""
import os
import sys
import traceback
from utils.path_manager import PathManager
from services.dataset_service import DatasetService
from services.file_service import FileService
from services.team_service import TeamService
from services.agent_service import AgentService
from services.map_service import MapService
from services.phase_service import PhaseService
from utils.exceptions import ServiceError

def init_services(_):  # Keep parameter for compatibility but don't use it
    """Initialize all services with minimal dependencies"""
    try:
        services = {
            'dataset_service': DatasetService(None),
            'file_service': FileService(None),
            'team_service': TeamService(None),
            'agent_service': AgentService(None),
            'map_service': MapService(None),
            'phase_service': PhaseService(None)
        }
        return services
        
    except Exception as e:
        print(f"Error initializing services: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise ServiceError(f"Service initialization failed: {str(e)}")
