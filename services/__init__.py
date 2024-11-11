"""Services package initialization"""
from services.dataset_service import DatasetService
from services.file_service import FileService
from services.mission_service import MissionService
from services.team_service import TeamService
from services.notification_service import NotificationService
from services.cache_service import CacheService
from services.agent_service import AgentService
from utils.exceptions import ServiceError

def init_services(web_instance):
    """Initialize all services for web interface"""
    try:
        # Initialize base services first
        web_instance.cache_service = CacheService(web_instance)
        web_instance.file_service = FileService(web_instance)
        web_instance.mission_service = MissionService()
        web_instance.notification_service = NotificationService(web_instance)
        
        # Initialize dataset service with validation
        try:
            web_instance.dataset_service = DatasetService(web_instance)
            if not web_instance.dataset_service.is_available():
                web_instance.logger.log("Dataset service initialization failed", 'warning')
        except Exception as e:
            web_instance.logger.log(f"Error initializing dataset service: {str(e)}", 'error')
            web_instance.dataset_service = None
        
        # Initialize team and agent services last
        web_instance.team_service = TeamService(web_instance)
        web_instance.agent_service = AgentService(web_instance)
        
        # Verify all services are properly initialized
        required_services = [
            'cache_service', 'file_service', 'mission_service',
            'notification_service', 'team_service', 'agent_service'
        ]
        
        missing_services = [svc for svc in required_services 
                          if not hasattr(web_instance, svc)]
        
        if missing_services:
            raise ServiceError(f"Failed to initialize services: {missing_services}")
            
        # Log successful initialization
        web_instance.logger.log("All services initialized successfully", 'success')
        
    except Exception as e:
        web_instance.logger.log(f"Error initializing services: {str(e)}", 'error')
        raise ServiceError(f"Service initialization failed: {str(e)}")
