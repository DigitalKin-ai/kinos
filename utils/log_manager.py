"""
LogManager - Simple console logging for Parallagon
"""
from datetime import datetime
import logging
from utils.exceptions import ParallagonError

class LogManager:
    """Basic console logging manager"""
    
    def __init__(self):
        """Initialize the logger"""
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger('Parallagon')
        self.logger.setLevel(logging.INFO)
        
    def log(self, message: str):
        """Log a message to console"""
        self.logger.info(message)
        
    def error(self, message: str):
        """Log an error message"""
        self.logger.error(message)
        
    def warning(self, message: str):
        """Log a warning message"""
        self.logger.warning(message)
