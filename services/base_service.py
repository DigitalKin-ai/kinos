from typing import Optional, Any
from utils.exceptions import ServiceError, ValidationError
from utils.logger import Logger

class BaseService:
    """Base class for all services providing common functionality"""
    
    def __init__(self, web_instance):
        self.web_instance = web_instance
        self.logger = Logger()
        
    def _validate_input(self, **kwargs) -> None:
        """Validate input parameters"""
        missing = [k for k, v in kwargs.items() if v is None]
        if missing:
            raise ValidationError(f"Missing required parameters: {', '.join(missing)}")
            
    def _handle_error(self, operation: str, error: Exception, 
                     default_value: Optional[Any] = None) -> Any:
        """Handle service operation errors consistently"""
        self.logger.log(f"Error in {operation}: {str(error)}", level='error')
        if default_value is not None:
            return default_value
        raise ServiceError(f"Failed to {operation}: {str(error)}")
        
    def _log_operation(self, operation: str, **kwargs) -> None:
        """Log service operations with relevant details"""
        details = ', '.join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.log(f"Executing {operation}: {details}", level='debug')
