import logging
import sys
from datetime import datetime

class CLILogger:
    def __init__(self, verbose=False, log_file=None):
        """
        Configurer le logging pour le CLI
        
        Args:
            verbose (bool): Mode débogage détaillé
            log_file (str, optional): Chemin du fichier de log
        """
        self.logger = logging.getLogger('kinos_cli')
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        
        # Configuration du format de log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Log console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Log fichier si spécifié
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message):
        self.logger.info(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def debug(self, message):
        self.logger.debug(message)
