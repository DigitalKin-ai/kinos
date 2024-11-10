import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler
from colorama import Fore, Style, init
from typing import Optional, Union

# Initialiser colorama pour le support des couleurs sur Windows
init(autoreset=True)

class AdvancedLogger:
    """Logger avancé avec support de la couleur et rotation de fichiers"""
    
    COLOR_MAP = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA
    }
    
    @classmethod
    def create(
        cls, 
        name: str, 
        log_file: Optional[str] = None, 
        level: int = logging.INFO,
        max_bytes: int = 10*1024*1024,  # 10 Mo
        backup_count: int = 5
    ) -> logging.Logger:
        """
        Créer un logger configurable
        
        Args:
            name (str): Nom du logger
            log_file (str, optional): Chemin du fichier de log
            level (int): Niveau de logging
            max_bytes (int): Taille maximale du fichier de log
            backup_count (int): Nombre de fichiers de backup
        
        Returns:
            logging.Logger: Logger configuré
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.handlers.clear()  # Nettoyer les handlers existants
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler console avec couleurs
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter(formatter))
        logger.addHandler(console_handler)
        
        # Handler de fichier avec rotation
        if log_file:
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    @classmethod
    def log(
        cls, 
        logger: logging.Logger, 
        message: str, 
        level: int = logging.INFO, 
        exc_info: Optional[Union[Exception, bool]] = None
    ):
        """
        Log un message avec gestion des exceptions
        
        Args:
            logger (logging.Logger): Logger à utiliser
            message (str): Message à logger
            level (int): Niveau de logging
            exc_info (Exception or bool, optional): Exception à logger
        """
        if exc_info:
            # Si exc_info est True, utiliser traceback
            if exc_info is True:
                message += f"\n{traceback.format_exc()}"
            # Si c'est une exception, formatter l'exception
            elif isinstance(exc_info, Exception):
                message += f"\n{traceback.format_exception_only(type(exc_info), exc_info)}"
        
        logger.log(level, message)

class ColoredFormatter(logging.Formatter):
    """Formatter avec support de la couleur"""
    def format(self, record):
        log_message = super().format(record)
        color = AdvancedLogger.COLOR_MAP.get(record.levelno, Fore.WHITE)
        return f"{color}{log_message}{Style.RESET_ALL}"
