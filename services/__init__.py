"""Services package initialization"""
import os
import traceback
from typing import Dict, Any, Optional
from utils.logger import Logger
from utils.exceptions import ServiceError
from services.team_service import TeamService
from utils.model_router import ModelRouter
from services.agent_service import AgentService
from services.map_service import MapService

# Use a more robust caching mechanism
_services_cache: Optional[Dict[str, Any]] = None
_configs_loaded = False

def init_services(_) -> Dict[str, Any]:
    """Initialize services"""
    logger = Logger()
    
    try:
        services = {}
        services['team_service'] = TeamService(None)
        services['model_router'] = ModelRouter()
        services['agent_service'] = AgentService(None)
        services['map_service'] = MapService(services['team_service'])
        
        return services
        
    except Exception as e:
        error_msg = (
            f"Error detecting team in {os.getcwd()}:\n"
            f"Error: {str(e)}\n"
            f"Trace: {traceback.format_exc()}"
        )
        logger.log(error_msg, 'error')
        raise ServiceError(error_msg)

    try:
        services = {}
        services['team_service'] = TeamService(None)
        services['model_router'] = ModelRouter()
        services['agent_service'] = AgentService(None)
        services['map_service'] = MapService(services['team_service'])
        
        return services
        
    except Exception as e:
        error_msg = (
            f"Error initializing services in {os.getcwd()}:\n"
            f"Error: {str(e)}\n"
            f"Trace: {traceback.format_exc()}"
        )
        logger.log(error_msg, 'error')
        raise ServiceError(error_msg)

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
