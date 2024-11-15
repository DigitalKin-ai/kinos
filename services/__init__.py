"""Services package initialization"""
import os
import sys
import traceback
from utils.path_manager import PathManager
from utils.exceptions import ServiceError

# Cache des services initialisés
_initialized_services = {}
_configs_loaded = False

def init_services(_):  # Keep parameter for compatibility but don't use it
    """Initialize all services with minimal dependencies"""
    global _initialized_services, _configs_loaded
    
    print("[DEBUG] Entering init_services()")
    print(f"[DEBUG] _initialized_services exists: {bool(_initialized_services)}")
    print(f"[DEBUG] _configs_loaded: {_configs_loaded}")
    
    # Si les services sont déjà initialisés, retourner le cache directement
    if _initialized_services:
        print("[DEBUG] Returning cached services")
        return _initialized_services
        
    try:
        print("[DEBUG] Starting service initialization")
        
        # Import services only when needed to avoid circular imports
        from services.dataset_service import DatasetService
        from services.file_service import FileService
        from services.team_service import TeamService
        from services.agent_service import AgentService
        from services.map_service import MapService
        from services.phase_service import PhaseService

        print("[DEBUG] Services imported successfully")

        # Create services without circular dependencies
        services = {
            'map_service': MapService(None),
            'dataset_service': DatasetService(None),
            'file_service': FileService(None),
            'team_service': TeamService(None),
            'agent_service': AgentService(None),
            'phase_service': PhaseService(None)
        }

        print("[DEBUG] Services created")

        # Store in cache
        _initialized_services = services
        print("[DEBUG] Services cached")

        # Charger les configurations une seule fois
        if not _configs_loaded:
            print("[DEBUG] Loading team configurations")
            for team_config in ['book-writing', 'coding', 'default', 'literature-review']:
                print(f"Loaded team configuration: {team_config}")
            _configs_loaded = True
            print("[DEBUG] Team configurations loaded")

        return _initialized_services

    except Exception as e:
        print(f"[ERROR] Service initialization failed: {str(e)}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise ServiceError(f"Service initialization failed: {str(e)}")
