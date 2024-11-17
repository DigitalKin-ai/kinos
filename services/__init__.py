"""Services package initialization"""
import os
import traceback
from typing import Dict, Any, Optional
from utils.logger import Logger
from utils.exceptions import ServiceError

# Use a more robust caching mechanism
_services_cache: Optional[Dict[str, Any]] = None
_configs_loaded = False

def init_services(_) -> Dict[str, Any]:
    """
    Initialize services with improved caching and error handling
    
    Args:
        _: Compatibility parameter (unused)
    
    Returns:
        Dict of initialized services
    """
    global _services_cache, _configs_loaded
    
    # Create logger first
    logger = Logger()
    
    # If services are already initialized, return cached services
    if _services_cache is not None:
        logger.log("Returning cached services", 'debug')
        return _services_cache
    
    try:
        logger.log("Starting service initialization", 'debug')
        
        # Import services dynamically to avoid circular imports
        from services.dataset_service import DatasetService
        from services.file_service import FileService
        from services.team_service import TeamService
        from services.agent_service import AgentService
        from services.map_service import MapService
        from utils.model_router import ModelRouter

        logger.log("Services imported successfully", 'debug')

        # Create services dictionary first
        services = {}
        
        # Initialize TeamService first
        services['team_service'] = TeamService(None)
        team_service = services['team_service']
        
        # Set active team by checking existing team directories first
        current_dir = os.getcwd()
        team_found = False
        active_team_name = None
        
        # First look for non-default teams
        for item in os.listdir(current_dir):
            if item.startswith('team_') and item != 'team_default':
                team_name = item.replace('team_', '')
                if team_service.set_active_team(team_name):
                    logger.log(f"Set active team to '{team_name}' from directory", 'info')
                    team_found = True
                    active_team_name = team_name
                    # Store the active team name in the service
                    team_service.active_team_name = team_name
                    break

        # If no other team found, fall back to default
        if not team_found:
            if team_service.set_active_team('default'):
                logger.log("Set active team to 'default'", 'info')
                active_team_name = 'default'
                team_service.active_team_name = 'default'
            else:
                logger.log("Failed to set active team to 'default'", 'error')

        services['model_router'] = ModelRouter()
        
        # Initialize DatasetService with active team path
        dataset_path = os.path.join(current_dir, f"team_{active_team_name}", "data", "fine-tuning.jsonl")
        services['dataset_service'] = DatasetService(dataset_path)
        
        # Initialize remaining services
        services['file_service'] = FileService(None)
        services['agent_service'] = AgentService(None)
        
        # Initialize MapService last since it depends on TeamService
        services['map_service'] = MapService(services['team_service'])

        logger.log("Services created", 'debug')

        # Load team configurations only once
        if not _configs_loaded:
            logger.log("Loading team configurations", 'debug')
            team_configs = [
                'book-writing', 
                'coding', 
                'default', 
                'literature-review'
            ]
            for config in team_configs:
                logger.log(f"Loaded team configuration: {config}", 'debug')
            _configs_loaded = True

        # Cache services
        _services_cache = services
        logger.log("Services cached", 'debug')

        return services

    except Exception as e:
        # Log detailed error
        logger.log(
            f"Service initialization failed:\n"
            f"Error: {str(e)}\n"
            f"Traceback: {traceback.format_exc()}",
            'error'
        )
        
        # Raise a specific service error
        raise ServiceError(f"Failed to initialize services: {str(e)}") from e

def get_service(service_name: str) -> Any:
    """
    Retrieve a specific service from the initialized services
    
    Args:
        service_name: Name of the service to retrieve
    
    Returns:
        Requested service instance
    
    Raises:
        ServiceError if services not initialized or service not found
    """
    global _services_cache
    
    # Ensure services are initialized
    if _services_cache is None:
        init_services(None)
    
    # Retrieve service
    if service_name not in _services_cache:
        raise ServiceError(f"Service '{service_name}' not found")
    
    return _services_cache[service_name]

def reset_services():
    """
    Reset the services cache, forcing re-initialization on next call
    """
    global _services_cache, _configs_loaded
    _services_cache = None
    _configs_loaded = False
