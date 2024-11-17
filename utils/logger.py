import logging

class Logger:
    """Utility class for handling logging operations."""
    
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('KinOS')
        
    def info(self, message):
        """Log info level message."""
        self.logger.info(message)
        
    def error(self, message):
        """Log error level message."""
        self.logger.error(message)
        
    def debug(self, message):
        """Log debug level message."""
        self.logger.debug(message)
        
    def warning(self, message):
        """Log warning level message."""
        self.logger.warning(message)
