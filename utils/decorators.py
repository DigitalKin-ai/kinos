import time
from functools import wraps

def safe_operation(max_retries=3, delay=1):
    """Decorator for safe operation execution with recovery
    
    Args:
        max_retries (int): Maximum number of retry attempts
        delay (int): Delay in seconds between retries
    """
    def decorator(operation_func):
        @wraps(operation_func)
        def wrapper(self, *args, **kwargs):
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    return operation_func(self, *args, **kwargs)
                except Exception as e:
                    retry_count += 1
                    self.log_message(
                        str(e),
                        operation=operation_func.__name__,
                        status=f"RETRY {retry_count}/{max_retries}"
                    )
                    
                    if retry_count == max_retries:
                        self.log_message(
                            "Operation failed permanently",
                            operation=operation_func.__name__,
                            status="FAILED"
                        )
                        raise
                    
                    time.sleep(delay)
                    
        return wrapper
    return decorator
