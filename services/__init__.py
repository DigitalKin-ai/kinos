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
                    
                if not os.path.exists(data_dir):
                    os.makedirs(data_dir)
                    print(f"Created data directory: {data_dir}")
                    
                # Create and verify service
                self.dataset_service = DatasetService(web_instance)
                print(f"Service created: {self.dataset_service is not None}")
                    
                # Verify availability
                available = self.dataset_service.is_available()
                print(f"Service available: {available}")
                    
                if not available:
                    print("Running availability check again with logging...")
                    self.dataset_service.is_available()  # Run again for logs
                    self.logger.log("Dataset service initialization failed", 'error')
                    raise ServiceError("Dataset service not available after initialization")
                    
                self.logger.log(
                    f"Dataset service initialized successfully\n"
                    f"Data directory: {self.dataset_service.data_dir}\n"
                    f"Dataset file: {self.dataset_service.dataset_file}",
                    'success'
                )
            except Exception as e:
                print(f"Error initializing dataset service: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                self.logger.log(f"Error initializing dataset service: {str(e)}", 'error')
                raise ServiceError(f"Dataset service initialization failed: {str(e)}")

        # Initialize core services
        services_to_init = [
            ('file_service', lambda: FileService(web_instance)),
            ('team_service', lambda: TeamService(web_instance)),
            ('agent_service', lambda: AgentService(web_instance)),
            ('map_service', lambda: MapService(web_instance)),
            ('phase_service', lambda: PhaseService(web_instance))
        ]

        # Only initialize services that don't already exist
        for service_name, init_func in services_to_init:
            if not hasattr(web_instance, service_name):
                try:
                    self.logger.log(f"Initializing {service_name}...", 'info')
                    setattr(web_instance, service_name, init_func())
                    
                    # Verify service was set
                    if not hasattr(web_instance, service_name):
                        raise ServiceError(f"Failed to set {service_name} on web_instance")
                    
                    # Verify service is not None
                    if getattr(web_instance, service_name) is None:
                        raise ServiceError(f"{service_name} was initialized as None")
                    
                    self.logger.log(f"Successfully initialized {service_name}", 'success')
                    
                except Exception as e:
                    self.logger.log(
                        f"Error initializing {service_name}:\n"
                        f"Error: {str(e)}\n"
                        f"Traceback: {traceback.format_exc()}", 
                        'error'
                    )
                    raise ServiceError(f"Failed to initialize {service_name}: {str(e)}")

        # Verify all required services are present
        required_services = [
            'dataset_service', 'file_service', 'team_service', 'agent_service',
            'map_service'
        ]
        
        missing_services = [svc for svc in required_services 
                          if not hasattr(web_instance, svc)]
        
        if missing_services:
            raise ServiceError(
                f"Missing required services after initialization: {missing_services}"
            )

        # Log successful initialization
        self.logger.log(
            "All services initialized successfully\n"
            f"Active services: {[svc for svc in required_services if hasattr(web_instance, svc)]}",
            'success'
        )
        
    except Exception as e:
        self.logger.log(
            f"Critical error in service initialization:\n"
            f"Error: {str(e)}\n"
            f"Traceback: {traceback.format_exc()}", 
            'critical'
        )
        raise ServiceError(f"Service initialization failed: {str(e)}")
