"""Services package initialization"""
import os
import sys
import traceback
from utils.path_manager import PathManager
from utils.exceptions import ServiceError

# Cache des services initialisés
_initialized_services = {}

def init_services(_):  # Keep parameter for compatibility but don't use it
    """Initialize all services with minimal dependencies"""
    
    # Si les services sont déjà initialisés, retourner le cache
    if _initialized_services:
        return _initialized_services
        
    try:
        # Import services only when needed to avoid circular imports
        from services.dataset_service import DatasetService
        from services.file_service import FileService
        from services.team_service import TeamService
        from services.agent_service import AgentService
        from services.map_service import MapService
        from services.phase_service import PhaseService

        # Create services without circular dependencies
        _initialized_services.update({
            'map_service': MapService(None),
            'dataset_service': DatasetService(None),
            'file_service': FileService(None),
            'team_service': TeamService(None),
            'agent_service': AgentService(None),
            'phase_service': PhaseService(None)
        })

        return _initialized_services

    except Exception as e:
        print(f"Error initializing services: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise ServiceError(f"Service initialization failed: {str(e)}")
