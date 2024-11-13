"""Timeout management utilities"""
import threading
import _thread
import functools
import contextlib
from typing import Callable, Any

class TimeoutManager:
    """Manages operation timeouts"""
    
    @staticmethod
    @contextlib.contextmanager 
    def timeout(seconds: int):
        """Context manager for timeouts"""
        timer = threading.Timer(seconds, lambda: _thread.interrupt_main())
        timer.start()
        try:
            yield
        except KeyboardInterrupt:
            raise TimeoutError(f"Operation timed out after {seconds} seconds")
        finally:
            timer.cancel()
            
    @staticmethod
    def with_timeout(seconds: int):
        """Decorator for adding timeout to functions"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                with TimeoutManager.timeout(seconds):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
