"""Services package initialization"""
import os
import traceback
from utils.path_manager import PathManager
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
        # Ensure web_instance has logger
        if not hasattr(web_instance, 'logger'):
            from utils.logger import Logger
            web_instance.logger = Logger()
            web_instance.logger.log("Created default logger", 'info')

        # Create data directory first
        try:
            data_dir = os.path.join(PathManager.get_project_root(), "data")
            os.makedirs(data_dir, exist_ok=True)
            web_instance.logger.log(f"Created/verified data directory: {data_dir}", 'info')
        except Exception as e:
            web_instance.logger.log(f"Error creating data directory: {str(e)}", 'error')
            raise

        # Initialize services in correct order with validation
        services_to_init = [
            ('cache_service', lambda: CacheService(web_instance)),
            ('file_service', lambda: FileService(web_instance)),
            ('mission_service', lambda: MissionService()),
            ('notification_service', lambda: NotificationService(web_instance)),
            ('dataset_service', lambda: DatasetService(web_instance)),
            ('team_service', lambda: TeamService(web_instance)),
            ('agent_service', lambda: AgentService(web_instance))
        ]

        for service_name, init_func in services_to_init:
            try:
                web_instance.logger.log(f"Initializing {service_name}...", 'info')
                setattr(web_instance, service_name, init_func())
                
                # Verify service was set
                if not hasattr(web_instance, service_name):
                    raise ServiceError(f"Failed to set {service_name} on web_instance")
                
                # Verify service is not None
                if getattr(web_instance, service_name) is None:
                    raise ServiceError(f"{service_name} was initialized as None")
                
                web_instance.logger.log(f"Successfully initialized {service_name}", 'success')
                
            except Exception as e:
                web_instance.logger.log(
                    f"Error initializing {service_name}:\n"
                    f"Error: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}", 
                    'error'
                )
                raise ServiceError(f"Failed to initialize {service_name}: {str(e)}")

        # Verify all required services are present
        required_services = [
            'cache_service', 'file_service', 'mission_service',
            'notification_service', 'dataset_service', 'team_service', 
            'agent_service'
        ]
        
        missing_services = [svc for svc in required_services 
                          if not hasattr(web_instance, svc)]
        
        if missing_services:
            raise ServiceError(
                f"Missing required services after initialization: {missing_services}"
            )

        # Verify dataset service specifically
        if not hasattr(web_instance, 'dataset_service'):
            raise ServiceError("Dataset service not initialized")
            
        if web_instance.dataset_service is None:
            raise ServiceError("Dataset service is None")
            
        if not web_instance.dataset_service.is_available():
            raise ServiceError("Dataset service is not available")

        # Log successful initialization
        web_instance.logger.log(
            "All services initialized successfully\n"
            f"Active services: {[svc for svc in required_services if hasattr(web_instance, svc)]}",
            'success'
        )
        
    except Exception as e:
        web_instance.logger.log(
            f"Critical error in service initialization:\n"
            f"Error: {str(e)}\n"
            f"Traceback: {traceback.format_exc()}", 
            'critical'
        )
        raise ServiceError(f"Service initialization failed: {str(e)}")
