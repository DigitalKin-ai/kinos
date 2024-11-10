import os
import time
import functools
from typing import Optional, Any, Tuple
from utils.exceptions import ServiceError, ValidationError
from utils.advanced_logger import AdvancedLogger
from config.global_config import GlobalConfig
from utils.logger import Logger  # Added import for Logger
import logging
import os

def retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    Décorateur de retry avec backoff exponentiel
    
    Args:
        max_attempts (int): Nombre maximum de tentatives
        delay (int): Délai initial entre les tentatives
        backoff (int): Facteur de backoff exponentiel
        exceptions (tuple): Types d'exceptions à gérer
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(self, *args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise
                    
                    # Log de l'erreur
                    self.logger.log(
                        f"Attempt {attempt} failed: {str(e)}. Retrying in {current_delay}s...", 
                        'warning'
                    )
                    
                    # Attente avec backoff
                    time.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator

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
        self.logger.log(f"Error in {operation}: {str(error)}", 'error')
        if default_value is not None:
            return default_value
        raise ServiceError(f"Failed to {operation}: {str(error)}")
        
    def _log_operation(self, operation: str, **kwargs) -> None:
        """Log service operations with relevant details"""
        details = ', '.join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.log(f"Executing {operation}: {details}", 'debug')
    
    @retry(max_attempts=3, delay=1, exceptions=(ServiceError, ConnectionError))
    def _safe_operation(self, operation):
        """
        Exécute une opération avec retry et gestion des erreurs
        
        Args:
            operation (callable): Opération à exécuter
        
        Returns:
            Résultat de l'opération
        """
        try:
            return operation()
        except Exception as e:
            self.logger.log(f"Operation failed: {str(e)}", 'error')
            raise

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
            self.logger.log(f"File operation {operation} completed in {duration:.3f}s", 'debug')
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log(f"File operation {operation} failed after {duration:.3f}s", 'error')
            raise ServiceError(f"Failed to {operation} file {file_path}: {str(e)}")

    def cleanup(self):
        """Base cleanup method for services"""
        try:
            # Implement basic cleanup
            if hasattr(self, '_cleanup_resources'):
                self._cleanup_resources()
                
            # Clear any caches or resources
            for attr in dir(self):
                if attr.endswith('_cache'):
                    cache = getattr(self, attr)
                    if isinstance(cache, dict):
                        cache.clear()
                        
        except Exception as e:
            self.logger.log(f"Error in base cleanup: {str(e)}", 'error')
