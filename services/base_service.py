import os
import time
import functools
from typing import Optional, Any
import traceback
from typing import Optional, Any
from utils.exceptions import ServiceError, ValidationError
from utils.logger import Logger

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
    
    def __init__(self, web_instance, team: str = None):
        """
        Initialize base service with team context
        
        Args:
            web_instance: Web instance for the service
            team: Team name/context for this service
        """
        self.logger = Logger()
        self._team = team  # Store team context
        self._web = web_instance
    def _validate_input(self, **kwargs) -> None:
        """Validate input parameters"""
        missing = [k for k, v in kwargs.items() if v is None]
        if missing:
            raise ValidationError(f"Missing required parameters: {', '.join(missing)}")
            
    @property
    def team(self) -> str:
        """Get current team context"""
        return self._team
        
    @team.setter 
    def team(self, value: str):
        """Set team context with validation"""
        if not value:
            self.logger.log("Attempt to set empty team context", 'warning')
            return
        self._team = value
        self.logger.log(f"Team context set to: {value}", 'debug')

    def _validate_team_context(self, operation: str):
        """Validate team context before operations"""
        if not self._team:
            raise ValueError(f"No team context for {operation}")

    def _handle_error(self, operation: str, error: Exception, 
                     default_value: Optional[Any] = None) -> Any:
        """Handle service operation errors consistently"""
        team_context = f" [team: {self._team}]" if self._team else ""
        self.logger.log(f"Error in {operation}{team_context}: {str(error)}", 'error')
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

    def _validate_path(self, path: str) -> bool:
        """Validation centralisée des chemins"""
        if not path or not isinstance(path, str):
            return False
        return os.path.exists(path) and os.access(path, os.R_OK | os.W_OK)

    def _validate_content(self, content: str) -> bool:
        """Validation centralisée du contenu"""
        return bool(content and content.strip())

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

    def _validate_path(self, path: str) -> bool:
        """Validation centralisée des chemins"""
        if not path or not isinstance(path, str):
            return False
        return os.path.exists(path) and os.access(path, os.R_OK | os.W_OK)

    def _validate_content(self, content: str) -> bool:
        """Validation centralisée du contenu"""
        return bool(content and content.strip())

    def cleanup(self):
        """Safe cleanup that never fails"""
        try:
            # Tenter le nettoyage mais ne jamais échouer
            if hasattr(self, 'mission_files'):
                self.mission_files.clear()
        except:
            pass
