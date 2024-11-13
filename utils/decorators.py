import functools
import time
import traceback
import contextlib
import threading
import _thread
from typing import Callable, Any, Optional
from utils.logger import Logger
from utils.exceptions import ServiceError, ValidationError

def safe_operation(
    max_retries: int = 3, 
    delay: float = 1.0, 
    backoff_factor: float = 2.0, 
    logger: Optional[Logger] = None
):
    """
    Advanced decorator for secure operation execution with enhanced error handling
    
    Args:
        max_retries (int): Maximum number of retry attempts
        delay (float): Initial delay between retries
        backoff_factor (float): Exponential backoff multiplier
        logger (Logger, optional): Custom logger instance
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use provided logger or create default
            log = logger or Logger()
            current_retry = 0
            current_delay = delay

            while current_retry < max_retries:
                try:
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # Reset metrics on success
                    if current_retry > 0:
                        log.log(
                            f"Operation {func.__name__} succeeded after {current_retry} retries", 
                            'success'
                        )
                    
                    return result

                except (ServiceError, ValidationError) as e:
                    # Specific errors that do not require retry
                    log.log(f"Non-retriable error in {func.__name__}: {str(e)}", 'error')
                    raise

                except Exception as e:
                    current_retry += 1
                    
                    # Detailed error logging
                    log.log(
                        f"Error in {func.__name__} (Attempt {current_retry}/{max_retries}): {str(e)}\n"
                        f"Traceback: {traceback.format_exc()}",
                        'warning'
                    )
                    
                    # Exponential backoff strategy
                    if current_retry < max_retries:
                        sleep_time = current_delay * (backoff_factor ** (current_retry - 1))
                        log.log(f"Retrying in {sleep_time:.2f} seconds", 'info')
                        time.sleep(sleep_time)
                    else:
                        # Last attempt
                        log.log(
                            f"Operation {func.__name__} failed after {max_retries} attempts", 
                            'error'
                        )
                        raise

            # If all attempts failed
            raise ServiceError(f"Operation {func.__name__} failed after {max_retries} attempts")
        
        return wrapper
    return decorator

