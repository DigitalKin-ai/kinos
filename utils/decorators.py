import time
from functools import wraps
from typing import Callable, Any

def safe_operation(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator for safely executing operations with retries
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    continue
                    
            # If we get here, all retries failed
            raise last_error
            
        return wrapper
    return decorator

