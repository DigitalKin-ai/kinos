"""Services package initialization"""
import os
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
        # Initialize base services first
        web_instance.cache_service = CacheService(web_instance)
        web_instance.file_service = FileService(web_instance)
        web_instance.mission_service = MissionService()
        web_instance.notification_service = NotificationService(web_instance)
        
        # Initialize dataset service with explicit logging and validation
        try:
            # Create data directory if it doesn't exist
            data_dir = os.path.join(PathManager.get_project_root(), "data")
            os.makedirs(data_dir, exist_ok=True)
            web_instance.logger.log(f"Created/verified data directory: {data_dir}", 'info')
            
            # Initialize dataset service with explicit configuration
            dataset_config = {
                'data_dir': data_dir,
                'dataset_file': 'fine-tuning.jsonl',
                'enabled': True  # Explicitly enable the service
            }
            
            web_instance.dataset_service = DatasetService(web_instance)
            
            # Verify service initialization
            if web_instance.dataset_service.is_available():
                web_instance.logger.log(
                    f"Dataset service initialized successfully\n"
                    f"Data directory: {data_dir}\n"
                    f"Dataset file: {os.path.join(data_dir, 'fine-tuning.jsonl')}", 
                    'info'
                )
            else:
                web_instance.logger.log(
                    "Dataset service initialization failed - service unavailable", 
                    'error'
                )
                
        except Exception as e:
            web_instance.logger.log(
                f"Critical error initializing dataset service:\n"
                f"Error: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}", 
                'error'
            )
            web_instance.dataset_service = None
        
        # Initialize team and agent services last
        web_instance.team_service = TeamService(web_instance)
        web_instance.agent_service = AgentService(web_instance)
        
        # Verify all services are properly initialized
        required_services = [
            'cache_service', 'file_service', 'mission_service',
            'notification_service', 'team_service', 'agent_service',
            'dataset_service'  # Add dataset_service to required list
        ]
        
        missing_services = [svc for svc in required_services 
                          if not hasattr(web_instance, svc)]
        
        if missing_services:
            web_instance.logger.log(
                f"Warning: Missing services: {missing_services}. "
                "Some functionality may be limited.",
                'warning'
            )
            
        # Log successful initialization
        web_instance.logger.log(
            f"Services initialized successfully. "
            f"Active services: {[svc for svc in required_services if hasattr(web_instance, svc)]}",
            'success'
        )
        
    except Exception as e:
        web_instance.logger.log(f"Critical error initializing services: {str(e)}", 'error')
        raise ServiceError(f"Service initialization failed: {str(e)}")
