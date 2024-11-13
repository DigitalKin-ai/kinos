from pathlib import Path
import os
import yaml
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GlobalConfig:
    """Global configuration management for KinOS"""
    
    # Base paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    MISSIONS_DIR = BASE_DIR / 'missions'
    LOGS_DIR = BASE_DIR / 'logs'
    TEMP_DIR = BASE_DIR / 'temp'
    CONFIG_DIR = BASE_DIR / 'config'
    PROMPTS_DIR = BASE_DIR / 'prompts'

    # API Keys with validation
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # Server Configuration
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', '8000'))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # Default configuration
    DEFAULT_CONFIG: Dict[str, Any] = {
        'core': {
            'verbose': False,
            'log_level': 'INFO',
            'max_retries': 3,
            'retry_delay': 1
        },
        'agents': {
            'default_model': 'anthropic/claude-3-5-haiku-20241022',
        },
        'teams': {
            'book-writing': {
                'log_directory': str(LOGS_DIR / 'book-writing')
            },
            'coding': {
                'log_directory': str(LOGS_DIR / 'coding')
            }
        },
        'paths': {
            'missions': str(MISSIONS_DIR),
            'logs': str(LOGS_DIR),
            'temp': str(TEMP_DIR),
            'prompts': str(PROMPTS_DIR)
        }
    }

    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist"""
        for directory in [cls.MISSIONS_DIR, cls.LOGS_DIR, cls.TEMP_DIR, 
                         cls.CONFIG_DIR, cls.PROMPTS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls) -> bool:
        """
        Validate critical configuration parameters
        
        Raises:
            ValueError: If critical configuration is missing
        """
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        # Validate directories exist
        cls.ensure_directories()
        
        # Validate port range
        if not 1 <= cls.PORT <= 65535:
            raise ValueError(f"Invalid port number: {cls.PORT}")
            
        return True

    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration with multiple priority levels
        
        Args:
            config_path: Optional path to custom config file
            
        Returns:
            Merged configuration dictionary
        """
        # Start with default config
        config = cls.DEFAULT_CONFIG.copy()
        
        # Possible config locations in priority order
        possible_configs = [
            config_path,
            Path.home() / '.kinos' / 'config.yaml',
            cls.CONFIG_DIR / 'kinos.yaml'
        ]
        
        # Load first found config file
        for path in possible_configs:
            if path and Path(path).exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        user_config = yaml.safe_load(f)
                        if user_config:
                            cls._deep_merge(config, user_config)
                    break
                except Exception as e:
                    logging.error(f"Error loading configuration: {e}")
        
        return config

    @staticmethod
    def _deep_merge(base: Dict, update: Dict) -> None:
        """
        Recursively merge dictionaries
        
        Args:
            base: Base dictionary to update
            update: Dictionary to merge in
        """
        for key, value in update.items():
            if isinstance(value, dict):
                base[key] = base.get(key, {})
                GlobalConfig._deep_merge(base[key], value)
            else:
                base[key] = value

    @classmethod
    def get_log_level(cls, config: Optional[Dict] = None) -> int:
        """
        Get logging level from configuration
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            logging level constant
        """
        config = config or cls.load_config()
        log_level_str = config['core'].get('log_level', 'INFO').upper()
        
        log_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        return log_levels.get(log_level_str, logging.INFO)
