"""
PathManager - Centralized path management and validation for KinOS
"""
import os
import sys
from typing import Optional, List
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

class PathManager:
    """
    Centralized path management with intelligent resolution and validation
    """
    
    @staticmethod
    def get_project_root() -> str:
        """Get the absolute path to the project root"""
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def get_missions_path() -> str:
        """Get path to missions directory"""
        return os.path.join(PathManager.get_project_root(), 'missions')

    @staticmethod
    def get_prompts_path() -> str:
        """Get path to prompts directory"""
        return os.path.join(PathManager.get_project_root(), 'prompts')

    @staticmethod
    def get_custom_prompts_path() -> str:
        """Get path to custom prompts directory"""
        custom_path = os.path.join(PathManager.get_prompts_path(), 'custom')
        os.makedirs(custom_path, exist_ok=True)
        return custom_path

    @staticmethod
    def get_logs_path() -> str:
        """Get path to logs directory"""
        return os.path.join(PathManager.get_project_root(), 'logs')

    @staticmethod
    def get_config_path() -> str:
        """Get path to config directory"""
        return os.path.join(PathManager.get_project_root(), 'config')

    @staticmethod
    def get_temp_path() -> str:
        """Get path to temporary files directory"""
        temp_path = os.path.join(PathManager.get_project_root(), 'temp')
        os.makedirs(temp_path, exist_ok=True)
        return temp_path

    @staticmethod
    def normalize_path(path: str) -> str:
        """
        Normalize a path, resolving symlinks and converting to absolute path
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized absolute path
        """
        return os.path.realpath(os.path.abspath(os.path.expanduser(path)))

    @staticmethod
    def validate_path(path: str, 
                      must_exist: bool = False, 
                      must_be_dir: bool = False, 
                      must_be_readable: bool = False, 
                      must_be_writable: bool = False) -> bool:
        """
        Comprehensive path validation
        
        Args:
            path: Path to validate
            must_exist: Path must exist
            must_be_dir: Path must be a directory
            must_be_readable: Path must be readable
            must_be_writable: Path must be writable
            
        Returns:
            bool: Whether path meets all specified criteria
        """
        try:
            normalized_path = PathManager.normalize_path(path)
            
            # Check existence
            if must_exist and not os.path.exists(normalized_path):
                return False
            
            # Check directory
            if must_be_dir and not os.path.isdir(normalized_path):
                return False
            
            # Check readability
            if must_be_readable and not os.access(normalized_path, os.R_OK):
                return False
            
            # Check writability
            if must_be_writable and not os.access(normalized_path, os.W_OK):
                return False
            
            return True
        except Exception:
            return False

    @staticmethod
    def get_ignored_paths(base_path: str = None) -> List[str]:
        """
        Get list of ignored paths based on .gitignore and .aiderignore
        
        Args:
            base_path: Base directory to search for ignore files
            
        Returns:
            List of ignored path patterns
        """
        base_path = base_path or os.getcwd()
        ignore_patterns = []
        
        for ignore_file in ['.gitignore', '.aiderignore']:
            ignore_path = os.path.join(base_path, ignore_file)
            if os.path.exists(ignore_path):
                try:
                    with open(ignore_path, 'r') as f:
                        patterns = f.readlines()
                    ignore_patterns.extend([p.strip() for p in patterns if p.strip() and not p.startswith('#')])
                except Exception:
                    pass
        
        return ignore_patterns

    @staticmethod
    def create_path_spec(base_path: str = None) -> Optional[PathSpec]:
        """
        Create a PathSpec from ignore files
        
        Args:
            base_path: Base directory to search for ignore files
            
        Returns:
            PathSpec object or None
        """
        ignore_patterns = PathManager.get_ignored_paths(base_path)
        return PathSpec.from_lines(GitWildMatchPattern, ignore_patterns) if ignore_patterns else None
</source>

2. `utils/decorators.py`:
<source>utils/decorators.py
<<<<<<< SEARCH
=======>
"""
Utility decorators for KinOS services and agents
"""
import functools
import time
import traceback
from typing import Callable, Any, Optional
from utils.logger import Logger

def safe_operation(max_retries: int = 3, 
                   delay: float = 1.0, 
                   backoff: float = 2.0, 
                   exceptions: tuple = (Exception,)):
    """
    Decorator for safe operation execution with retry and error handling
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries
        backoff: Exponential backoff factor
        exceptions: Tuple of exception types to catch
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = Logger()
            current_delay = delay
            
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    if attempt == max_retries:
                        logger.log(
                            f"Operation {func.__name__} failed after {max_retries} attempts: {str(e)}", 
                            'error'
                        )
                        raise
                    
                    logger.log(
                        f"Attempt {attempt} of {func.__name__} failed: {str(e)}. "
                        f"Retrying in {current_delay:.2f}s", 
                        'warning'
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
        
        return wrapper
    return decorator

def timeout(seconds: int = 30):
    """
    Decorator to set a timeout for a function
    
    Args:
        seconds: Maximum execution time in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from concurrent.futures import ThreadPoolExecutor, TimeoutError
            
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    result = future.result(timeout=seconds)
                    return result
                except TimeoutError:
                    logger = Logger()
                    logger.log(
                        f"Function {func.__name__} timed out after {seconds} seconds", 
                        'warning'
                    )
                    raise TimeoutError(f"Function {func.__name__} timed out")
        
        return wrapper
    return decorator

def log_method_call(log_level: str = 'debug'):
    """
    Decorator to log method calls with arguments and return values
    
    Args:
        log_level: Logging level (debug/info/warning/error)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = Logger()
            
            # Log method entry
            logger.log(
                f"Entering {func.__name__} with args: {args}, kwargs: {kwargs}", 
                log_level
            )
            
            try:
                result = func(*args, **kwargs)
                
                # Log method exit and return value
                logger.log(
                    f"Exiting {func.__name__} with result: {result}", 
                    log_level
                )
                
                return result
            
            except Exception as e:
                logger.log(
                    f"Exception in {func.__name__}: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}", 
                    'error'
                )
                raise
        
        return wrapper
    return decorator
</source>

3. `utils/exceptions.py`:
<source>utils/exceptions.py
<<<<<<< SEARCH
