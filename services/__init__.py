"""Services package initialization"""
import os
import sys
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
    """Initialize all services with detailed logging"""
    try:
        print("\n=== STARTING SERVICE INITIALIZATION ===")
        
        # Ensure web_instance has logger
        if not hasattr(web_instance, 'logger'):
            from utils.logger import Logger
            web_instance.logger = Logger()
            print("Created new logger for web_instance")

        # Skip DatasetService initialization if it already exists AND is available
        if hasattr(web_instance, 'dataset_service') and web_instance.dataset_service:
            if web_instance.dataset_service.is_available():
                print("Dataset service already initialized and available")
            else:
                print("Dataset service exists but not available - reinitializing")
                web_instance.dataset_service = DatasetService(web_instance)
        else:
            print("\n=== DATASET SERVICE INITIALIZATION ===")
            try:
                # Verify data path
                data_dir = os.path.join(PathManager.get_project_root(), "data")
                print(f"Data directory path: {data_dir}")
                print(f"Directory exists: {os.path.exists(data_dir)}")
                    
                if not os.path.exists(data_dir):
                    os.makedirs(data_dir)
                    print(f"Created data directory: {data_dir}")
                    
                # Create and verify service
                web_instance.dataset_service = DatasetService(web_instance)
                print(f"Service created: {web_instance.dataset_service is not None}")
                    
                # Verify availability
                available = web_instance.dataset_service.is_available()
                print(f"Service available: {available}")
                    
                if not available:
                    print("Running availability check again with logging...")
                    web_instance.dataset_service.is_available()  # Run again for logs
                    web_instance.logger.log("Dataset service initialization failed", 'error')
                    raise ServiceError("Dataset service not available after initialization")
                    
                print(f"Data directory: {web_instance.dataset_service.data_dir}")
                print(f"Dataset file: {web_instance.dataset_service.dataset_file}")
                    
                web_instance.logger.log(
                    f"Dataset service initialized successfully\n"
                    f"Data directory: {web_instance.dataset_service.data_dir}\n"
                    f"Dataset file: {web_instance.dataset_service.dataset_file}",
                    'success'
                )
            except Exception as e:
                print(f"Error initializing dataset service: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                web_instance.logger.log(f"Error initializing dataset service: {str(e)}", 'error')
                raise ServiceError(f"Dataset service initialization failed: {str(e)}")

        # Initialize remaining services only if dataset service is available
        if not hasattr(web_instance, 'dataset_service') or not web_instance.dataset_service.is_available():
            raise ServiceError("Dataset service must be initialized and available before other services")

        # Continue with other services...
        services_to_init = [
            ('cache_service', lambda: CacheService(web_instance)),
            ('file_service', lambda: FileService(web_instance)),
            ('mission_service', lambda: MissionService()),
            ('notification_service', lambda: NotificationService(web_instance)),
            ('team_service', lambda: TeamService(web_instance)),
            ('agent_service', lambda: AgentService(web_instance))
        ]

        # Only initialize services that don't already exist
        for service_name, init_func in services_to_init:
            if not hasattr(web_instance, service_name):
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
