import os
import sys
import logging
from datetime import datetime
from typing import Optional
from utils.path_manager import PathManager
import threading

class Logger:
    """Simplified logging with colors and thread-safe output"""
    
    COLORS = {
        'info': '\033[94m',    # Blue
        'success': '\033[92m', # Green
        'warning': '\033[93m', # Yellow
        'error': '\033[91m',   # Red
        'reset': '\033[0m'     # Reset
    }

    def __init__(self):
        """Initialize logger with thread lock"""
        self.is_tty = sys.stdout.isatty()
        self._log_lock = threading.Lock()
        self._shutting_down = False
        self._level = logging.INFO  # Default level
        self.last_message = ""  # Track last logged message
        # Register cleanup at exit
        import atexit
        atexit.register(self._cleanup)

    def set_level(self, level):
        """Set the logging level
        
        Args:
            level: Either a string level name or logging constant
        """
        if isinstance(level, str):
            # Convert string level to logging constant
            level_map = {
                'DEBUG': logging.DEBUG,
                'INFO': logging.INFO,
                'SUCCESS': logging.INFO,  # Map SUCCESS to INFO
                'WARNING': logging.WARNING, 
                'ERROR': logging.ERROR,
                'CRITICAL': logging.CRITICAL
            }
            self._level = level_map.get(level.upper(), logging.INFO)
        else:
            # Already a logging constant
            self._level = level
        
        # Log level change
        print(f"Log level set to: {level}")

    def _cleanup(self):
        """Mark logger as shutting down and flush output"""
        try:
            self._shutting_down = True
            # Flush output streams directly instead of calling self.flush()
            with self._log_lock:
                if hasattr(sys.stdout, 'flush'):
                    sys.stdout.flush()
                if hasattr(sys.stderr, 'flush'):
                    sys.stderr.flush()
        except:
            pass  # Ignore errors during shutdown

    def log(self, message: str, level: str = 'info'):
        """Thread-safe logging with level filtering and shutdown handling"""
        if self._shutting_down:
            return  # Skip logging during shutdown

        # Map string levels to logging constants
        level_map = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL,
            'success': logging.INFO  # Success mapped to INFO for compatibility
        }
        
        # Get numeric level, default to INFO if level string not recognized
        msg_level = level_map.get(level.lower(), logging.INFO)
        
        # Always show success messages, otherwise check level
        if level.lower() != 'success' and msg_level < self._level:
            return
            
        try:
            with self._log_lock:
                timestamp = datetime.now().strftime("%H:%M:%S")
                formatted = f"[{timestamp}] [{level.upper()}] {message}"
                
                # Store last message before formatting
                self.last_message = message
                
                if self.is_tty:
                    color = self.COLORS.get(level, self.COLORS['info'])
                    # Use print() with width=None to prevent truncation
                    print(f"{color}{formatted}{self.COLORS['reset']}", flush=True, end='\n', width=None)
                else:
                    print(formatted, flush=True, end='\n', width=None)
                
        except Exception:
            # During shutdown, some exceptions are expected
            if not self._shutting_down:
                # Only print error if not shutting down
                print(f"Logging error for message: {message}")

def configure_cli_logger(force_color=None, log_level='INFO'):
    """
    Configure CLI logger with intelligent color detection and log level
    
    Args:
        force_color (bool, optional): 
            - True: Force color output
            - False: Disable color output
            - None: Auto-detect
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger instance with appropriate color configuration
    """
    # Create logger instance
    logger = Logger()
    
    # Set log level - Convert string level to logging constant
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    logger.set_level(level_map.get(log_level.upper(), logging.INFO))
    
    return logger
    
    def _should_colorize(self):
        """Determine if colors should be applied"""
        return self.force_color or (self.is_tty and 'TERM' in os.environ)
    
    def __str__(self):
        return self._name
        
    def __repr__(self):
        return self._name
    
    def log(self, message: str, level: str = 'info', **kwargs):
        """Main logging method that handles all cases"""
        try:
            # Always remove level from kwargs to prevent duplicates
            kwargs.pop('level', None)
            
            # Extract file_path from kwargs
            file_path = kwargs.pop('file_path', None)
            
            # Get timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Prepare log message
            formatted_message = f"[{timestamp}] [{level.upper()}] {message}"
            
            # Colorize if appropriate
            if self._should_colorize():
                color = self.COLORS.get(level, self.COLORS['info'])
                reset = self.COLORS['reset']
                colored_message = f"{color}{formatted_message}{reset}"
                print(colored_message)
            else:
                # Plain text for non-TTY or when color is disabled
                print(formatted_message)
            
            # File logging remains the same
            if not file_path:
                file_path = os.path.join(PathManager.get_logs_path(), 'agent_operations.log')
                
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"{formatted_message}\n")
                
        except Exception as e:
            # Fallback logging
            print(f"Logging error: {e}")
            print(f"Original message: {message}")
    
    def __call__(self, message: str, level: str = 'info', **kwargs):
        """Unified call method that handles all logging patterns"""
        # Remove level from kwargs to avoid duplicate
        kwargs.pop('level', None)
        self.log(message, level, **kwargs)

    def log_commit(self, agent: str, commit_hash: str, message: str, emoji: str):
        """Log a commit with consistent formatting"""
        formatted = f"[{agent}] {emoji} {commit_hash}: {message}"
        self.log(formatted, 'info')

    def log_path_operation(self, operation: str, path: str, success: bool, error: Optional[str] = None):
        """
        Log file/path operations with consistent formatting
        
        Args:
            operation: Type of operation (read/write/create/etc)
            path: Path being operated on
            success: Whether operation succeeded
            error: Optional error message
        """
        try:
            # Format relative path for cleaner output
            rel_path = os.path.relpath(path, os.getcwd())
            
            if success:
                self.log(f"✓ {operation}: {rel_path}", 'success')
            else:
                error_msg = f" ({error})" if error else ""
                self.log(f"❌ {operation} failed: {rel_path}{error_msg}", 'error')
                
        except Exception as e:
            # Fallback to full path if relative path fails
            if success:
                self.log(f"✓ {operation}: {path}", 'success')
            else:
                error_msg = f" ({error})" if error else ""
                self.log(f"❌ {operation} failed: {path}{error_msg}", 'error')

    def log_path_validation(self, path: str, valid: bool, reason: Optional[str] = None):
        """
        Log path validation results
        
        Args:
            path: Path being validated
            valid: Whether path is valid
            reason: Optional reason for invalid path
        """
        try:
            rel_path = os.path.relpath(path, os.getcwd())
            
            if valid:
                self.log(f"✓ Valid path: {rel_path}", 'success')
            else:
                reason_msg = f" ({reason})" if reason else ""
                self.log(f"❌ Invalid path: {rel_path}{reason_msg}", 'error')
                
        except Exception as e:
            # Fallback to full path
            if valid:
                self.log(f"✓ Valid path: {path}", 'success')
            else:
                reason_msg = f" ({reason})" if reason else ""
                self.log(f"❌ Invalid path: {path}{reason_msg}", 'error')

    def log_path_change(self, old_path: str, new_path: str, success: bool, error: Optional[str] = None):
        """
        Log path change operations
        
        Args:
            old_path: Original path
            new_path: New path
            success: Whether change succeeded
            error: Optional error message
        """
        try:
            rel_old = os.path.relpath(old_path, os.getcwd())
            rel_new = os.path.relpath(new_path, os.getcwd())
            
            if success:
                self.log(f"✓ Path changed: {rel_old} → {rel_new}", 'success')
            else:
                error_msg = f" ({error})" if error else ""
                self.log(f"❌ Path change failed: {rel_old} → {rel_new}{error_msg}", 'error')
                
        except Exception as e:
            # Fallback to full paths
            if success:
                self.log(f"✓ Path changed: {old_path} → {new_path}", 'success')
            else:
                error_msg = f" ({error})" if error else ""
                self.log(f"❌ Path change failed: {old_path} → {new_path}{error_msg}", 'error')

    def _log(self, message: str, level: str = 'info', **kwargs):
        """Internal logging method"""
        # Remove level from kwargs to avoid duplicate
        kwargs.pop('level', None)
        # Call log() without explicitly passing level as kwarg
        self.log(message, level, **kwargs)
        
