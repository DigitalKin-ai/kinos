import logging
from colorama import init, Fore, Style

class Logger:
    """Utility class for handling logging operations."""
    
    def __init__(self):
        # Initialize colorama for cross-platform color support
        init()
        
        # Custom formatter with colors
        class ColorFormatter(logging.Formatter):
            FORMATS = {
                logging.DEBUG: Fore.CYAN + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
                logging.INFO: Fore.GREEN + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
                logging.WARNING: Fore.YELLOW + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
                logging.ERROR: Fore.RED + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
                logging.CRITICAL: Fore.RED + Style.BRIGHT + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL
            }

            def format(self, record):
                log_fmt = self.FORMATS.get(record.levelno)
                formatter = logging.Formatter(log_fmt)
                return formatter.format(record)

        # Setup handler with color formatter
        handler = logging.StreamHandler()
        handler.setFormatter(ColorFormatter())
        
        # Configure logger
        self.logger = logging.getLogger('KinOS')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers and add our colored handler
        self.logger.handlers = []
        self.logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
        
    def info(self, message):
        """Log info level message in green."""
        self.logger.info(message)
        
    def error(self, message):
        """Log error level message in red."""
        self.logger.error(message)
        
    def debug(self, message):
        """Log debug level message in cyan."""
        self.logger.debug(message)
        
    def warning(self, message):
        """Log warning level message in yellow."""
        self.logger.warning(message)
