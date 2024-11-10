from pathlib import Path
import os
import yaml
import logging

class GlobalConfig:
    """Configuration globale centralisée pour KinOS"""
    
    # Chemins de base
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Répertoires standards
    MISSIONS_DIR = BASE_DIR / 'missions'
    LOGS_DIR = BASE_DIR / 'logs'
    TEMP_DIR = BASE_DIR / 'temp'
    CONFIG_DIR = BASE_DIR / 'config'
    
    # Configuration par défaut
    DEFAULT_CONFIG = {
        'core': {
            'verbose': False,
            'log_level': 'INFO',
            'timeout': 3600,  # 1 heure
            'max_retries': 3
        },
        'teams': {
            'book-writing': {
                'default_timeout': 3600,
                'log_directory': str(LOGS_DIR / 'book-writing')
            },
            'coding': {
                'default_timeout': 7200,
                'log_directory': str(LOGS_DIR / 'coding')
            }
        },
        'paths': {
            'missions': str(MISSIONS_DIR),
            'logs': str(LOGS_DIR),
            'temp': str(TEMP_DIR)
        }
    }
    
    @classmethod
    def ensure_directories(cls):
        """Créer les répertoires nécessaires s'ils n'existent pas"""
        for directory in [cls.MISSIONS_DIR, cls.LOGS_DIR, cls.TEMP_DIR, cls.CONFIG_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def load_config(cls, config_path=None):
        """
        Charger la configuration avec plusieurs niveaux de priorité
        
        Args:
            config_path (str, optional): Chemin vers un fichier de configuration personnalisé
        
        Returns:
            dict: Configuration fusionnée
        """
        # Configuration par défaut
        config = cls.DEFAULT_CONFIG.copy()
        
        # Chemins de configuration possibles
        possible_configs = [
            config_path,
            Path.home() / '.kinos' / 'config.yaml',
            cls.CONFIG_DIR / 'kinos.yaml'
        ]
        
        # Charger la première configuration trouvée
        for path in possible_configs:
            if path and Path(path).exists():
                try:
                    with open(path, 'r') as f:
                        user_config = yaml.safe_load(f)
                        cls._deep_merge(config, user_config)
                    break
                except Exception as e:
                    print(f"Erreur lors du chargement de la configuration : {e}")
        
        return config
    
    @staticmethod
    def _deep_merge(base, update):
        """
        Fusion récursive de dictionnaires
        
        Args:
            base (dict): Dictionnaire de base
            update (dict): Dictionnaire à fusionner
        """
        for key, value in update.items():
            if isinstance(value, dict):
                base[key] = base.get(key, {})
                GlobalConfig._deep_merge(base[key], value)
            else:
                base[key] = value
