import os
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

    def _validate_file_path(self, file_path: str) -> None:
        """Validate file path exists and is accessible"""
        if not os.path.exists(file_path):
            raise ValidationError(f"File not found: {file_path}")
        if not os.access(file_path, os.R_OK):
            raise ValidationError(f"File not readable: {file_path}")

    def _ensure_directory(self, directory: str) -> None:
        """Ensure directory exists, create if needed"""
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            raise ServiceError(f"Failed to create directory {directory}: {str(e)}")

    def _safe_file_operation(self, operation: str, file_path: str, 
                            mode: str = 'r', encoding: str = 'utf-8'):
        """Context manager for safe file operations with performance metrics"""
        start_time = time.time()
        try:
            with open(file_path, mode, encoding=encoding) as f:
                yield f
            duration = time.time() - start_time
            self.logger.log(f"File operation {operation} completed in {duration:.3f}s", level='debug')
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log(f"File operation {operation} failed after {duration:.3f}s", level='error')
            raise ServiceError(f"Failed to {operation} file {file_path}: {str(e)}")
