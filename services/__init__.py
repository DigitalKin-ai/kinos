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
    
    # Get current team - throw error if none found
    try:
        current_dir = os.getcwd()  # Use actual working directory
        logger.log(f"Initializing services in: {current_dir}", 'debug')
        
        team_dir = next((d for d in os.listdir(current_dir) if d.startswith('team_')), None)
        if not team_dir:
            error_msg = (
                f"No team directory found in {current_dir}\n"
                "Available directories: " + ", ".join(os.listdir(current_dir))
            )
            logger.log(error_msg, 'error')
            raise ServiceError(
                f"{error_msg}\n"
                "Please create a team directory (team_*) in the current working directory before running KinOS"
            )
        
        current_team = team_dir[5:]  # Remove 'team_' prefix
        logger.log(f"Found team directory: {team_dir}", 'debug')
        
    except Exception as e:
        error_msg = (
            f"Error detecting team in {os.getcwd()}:\n"
            f"Error: {str(e)}\n"
            f"Trace: {traceback.format_exc()}"
        )
        logger.log(error_msg, 'error')
        raise ServiceError(error_msg)

    # Return cached services if team hasn't changed
    if _services_cache is not None and getattr(_services_cache.get('team_service'), 'active_team_name', None) == current_team:
        logger.log(f"Returning cached services for team: {current_team}", 'debug')
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
        
        # Only set active team if a team directory exists
        if current_team:
            team_service.set_active_team(current_team)
            logger.log(f"Set active team to '{current_team}' from directory", 'info')

        services['model_router'] = ModelRouter()
        
        # Initialize DatasetService with active team path if available
        team_service = services['team_service']
        active_team = team_service.get_active_team() if team_service.active_team_name else None
        team_name = active_team.get('name') if active_team else None
        
        if team_name:
            dataset_path = os.path.join(current_dir, f"team_{team_name}", "data", "fine-tuning.jsonl")
            services['dataset_service'] = DatasetService(dataset_path)
        else:
            services['dataset_service'] = DatasetService(None)
        
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
