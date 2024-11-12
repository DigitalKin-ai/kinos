import os
import json
import traceback
from typing import Optional, Dict, Any

class PathManager:
    """Centralized and secure path management for KinOS"""
    
    _CONFIG_FILE = 'config/missions.json'
    _DEFAULT_MISSIONS_DIR = os.path.expanduser('~/KinOS_Missions')
    
    @classmethod
    def get_project_root(cls) -> str:
        """Returns the absolute path to the project root with robust detection"""
        try:
            # Current file's directory
            current = os.path.abspath(__file__)
            
            # Detection strategies
            strategies = [
                # Strategy 1: Look for key directories
                lambda path: any(os.path.exists(os.path.join(path, d)) 
                                 for d in ["missions", "config", "agents", "services", "routes"]),
                
                # Strategy 2: Look for specific project files
                lambda path: any(os.path.exists(os.path.join(path, f)) 
                                 for f in ['kinos_cli.py', 'kinos_web.py', 'requirements.txt', '.env'])
            ]
            
            # Traverse up the directory tree
            while current != os.path.dirname(current):
                for strategy in strategies:
                    if strategy(current):
                        return current
                current = os.path.dirname(current)
            
            # Fallback strategies
            fallback_paths = [
                os.path.dirname(os.path.abspath(__file__)),  # directory of path_manager.py
                os.getcwd(),  # current working directory
                os.path.expanduser('~/KinOS')  # potential project directory
            ]
            
            for path in fallback_paths:
                if os.path.exists(path):
                    return path
            
            raise ValueError(f"Project root not found. Current path: {current}")
        
        except Exception as e:
            print(f"Project root detection failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            raise

    @classmethod
    def _load_mission_config(cls) -> Dict[str, Any]:
        """Load mission configurations from JSON"""
        try:
            config_path = os.path.join(cls.get_project_root(), cls._CONFIG_FILE)
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading mission config: {e}")
            return {}

    @classmethod
    def get_mission_path(cls, mission_name: str, base_path: Optional[str] = None) -> str:
        """
        Get the absolute path for a mission with enhanced validation
        
        Args:
            mission_name (str): Name of the mission
            base_path (Optional[str]): Custom base path for missions
        
        Returns:
            str: Absolute path to the mission directory
        """
        # Validate mission name
        if not mission_name or not isinstance(mission_name, str):
            raise ValueError("Invalid mission name")
        
        # Normalize mission name for filesystem
        normalized_name = cls._normalize_mission_name(mission_name)
        
        # Determine base path with priority:
        # 1. Explicitly provided base path
        # 2. Path from mission configuration
        # 3. Default missions directory
        if base_path:
            mission_path = os.path.abspath(os.path.join(base_path, normalized_name))
        else:
            mission_config = cls._load_mission_config()
            if mission_name in mission_config and 'path' in mission_config[mission_name]:
                mission_path = os.path.abspath(mission_config[mission_name]['path'])
            else:
                # Use default missions directory, creating if it doesn't exist
                os.makedirs(cls._DEFAULT_MISSIONS_DIR, exist_ok=True)
                mission_path = os.path.join(cls._DEFAULT_MISSIONS_DIR, normalized_name)
        
        # Validate mission path
        if not cls.validate_mission_path(mission_path):
            raise ValueError(f"Invalid mission path: {mission_path}")
        
        # Ensure mission directory exists
        os.makedirs(mission_path, exist_ok=True)
        
        return mission_path

    @staticmethod
    def _normalize_mission_name(mission_name: str) -> str:
        """
        Normalize mission name for filesystem use
        
        Args:
            mission_name (str): Original mission name
        
        Returns:
            str: Normalized mission name
        """
        # Replace invalid filesystem characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        normalized = mission_name.lower()
        for char in invalid_chars:
            normalized = normalized.replace(char, '_')
        
        # Remove multiple consecutive underscores
        while '__' in normalized:
            normalized = normalized.replace('__', '_')
        
        # Remove leading/trailing underscores and whitespace
        return normalized.strip('_').strip()

    @classmethod
    def validate_mission_path(cls, path: str) -> bool:
        """
        Validate a mission path with comprehensive checks
        
        Args:
            path (str): Path to validate
        
        Returns:
            bool: Whether the path is valid
        """
        try:
            # Ensure absolute path
            if not os.path.isabs(path):
                return False
            
            # Ensure path is not within project root
            project_root = cls.get_project_root()
            if path.startswith(project_root):
                return False
            
            # Check path exists or is creatable
            try:
                # Attempt to create directory if it doesn't exist
                os.makedirs(path, exist_ok=True)
            except (PermissionError, OSError):
                return False
            
            # Check read and write permissions
            if not os.access(path, os.R_OK | os.W_OK):
                return False
            
            return True
        
        except Exception:
            return False

    @classmethod
    def list_missions(cls, base_path: Optional[str] = None) -> Dict[str, str]:
        """
        List all available missions
        
        Args:
            base_path (Optional[str]): Custom base path to search for missions
        
        Returns:
            Dict[str, str]: Dictionary of mission names and their paths
        """
        missions = {}
        
        # Use provided base path or default missions directory
        search_path = base_path or cls._DEFAULT_MISSIONS_DIR
        
        try:
            for mission_name in os.listdir(search_path):
                mission_path = os.path.join(search_path, mission_name)
                if os.path.isdir(mission_path) and cls.validate_mission_path(mission_path):
                    missions[mission_name] = mission_path
        except Exception as e:
            print(f"Error listing missions: {e}")
        
        return missions

    @staticmethod
    def get_prompts_path() -> str:
        """Retourne le chemin vers le dossier des prompts"""
        return os.path.join(PathManager.get_project_root(), "prompts")

    @staticmethod
    def get_config_path() -> str:
        """Retourne le chemin vers le dossier de configuration"""
        return os.path.join(PathManager.get_project_root(), "config")

    @staticmethod
    def get_templates_path() -> str:
        """Retourne le chemin vers le dossier des templates"""
        return os.path.join(PathManager.get_project_root(), "templates")

    @staticmethod
    def get_static_path() -> str:
        """Retourne le chemin vers le dossier static"""
        return os.path.join(PathManager.get_project_root(), "static")

    @staticmethod
    def get_logs_path() -> str:
        """Retourne le chemin vers le dossier des logs"""
        logs_dir = os.path.join(PathManager.get_project_root(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        return logs_dir

    @staticmethod
    def get_temp_path() -> str:
        """Retourne le chemin vers le dossier temp"""
        temp_dir = os.path.join(PathManager.get_project_root(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    @staticmethod
    def get_temp_file(prefix: str = "", suffix: str = "", subdir: str = "") -> str:
        """Crée un chemin de fichier temporaire avec sous-dossier optionnel"""
        import uuid
        temp_dir = PathManager.get_temp_path()
        if subdir:
            temp_dir = os.path.join(temp_dir, subdir)
            os.makedirs(temp_dir, exist_ok=True)
        return os.path.join(temp_dir, f"{prefix}{uuid.uuid4()}{suffix}")

    @staticmethod
    def get_backup_path() -> str:
        """Retourne le chemin vers le dossier des backups"""
        backup_dir = os.path.join(PathManager.get_project_root(), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    @staticmethod
    def get_config_file_path(filename: str) -> str:
        """Retourne le chemin vers un fichier de configuration"""
        return os.path.join(PathManager.get_config_path(), filename)

    @staticmethod
    def get_static_file_path(filename: str) -> str:
        """Retourne le chemin vers un fichier statique"""
        return os.path.join(PathManager.get_static_path(), filename)

    @staticmethod
    def get_log_file_path(log_type: str) -> str:
        """Retourne le chemin vers un fichier de log spécifique"""
        logs_dir = PathManager.get_logs_path()
        return os.path.join(logs_dir, f"{log_type}.log")

    @staticmethod
    def get_custom_prompts_path() -> str:
        """Retourne le chemin vers les prompts personnalisés"""
        custom_prompts = os.path.join(PathManager.get_prompts_path(), "custom")
        os.makedirs(custom_prompts, exist_ok=True)
        return custom_prompts

    @staticmethod
    def get_cache_file_path(cache_key: str) -> str:
        """Retourne le chemin vers un fichier de cache"""
        cache_dir = os.path.join(PathManager.get_temp_path(), "cache")
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, f"{cache_key}.cache")

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalise un chemin de fichier"""
        return os.path.normpath(os.path.abspath(path))

    @staticmethod
    def get_agents_path() -> str:
        """Retourne le chemin vers le dossier des agents"""
        return os.path.join(PathManager.get_project_root(), "agents")

    @staticmethod
    def get_services_path() -> str:
        """Retourne le chemin vers le dossier des services"""
        return os.path.join(PathManager.get_project_root(), "services")

    @staticmethod
    def get_routes_path() -> str:
        """Retourne le chemin vers le dossier des routes"""
        return os.path.join(PathManager.get_project_root(), "routes")

    @staticmethod
    def get_docs_path() -> str:
        """Retourne le chemin vers le dossier de documentation"""
        docs_dir = os.path.join(PathManager.get_project_root(), "docs")
        os.makedirs(docs_dir, exist_ok=True)
        return docs_dir

    @staticmethod
    def get_tests_path() -> str:
        """Retourne le chemin vers le dossier des tests"""
        tests_dir = os.path.join(PathManager.get_project_root(), "tests")
        os.makedirs(tests_dir, exist_ok=True)
        return tests_dir

    @staticmethod
    def get_config_file(filename: str) -> str:
        """Retourne le chemin vers un fichier de configuration spécifique"""
        return os.path.join(PathManager.get_config_path(), filename)

    @staticmethod
    def get_prompt_file(agent_name: str) -> str:
        """Retourne le chemin vers le fichier prompt d'un agent"""
        return os.path.join(PathManager.get_prompts_path(), f"{agent_name}.md")

    @staticmethod
    def get_log_file(service_name: str) -> str:
        """Retourne le chemin vers un fichier de log spécifique"""
        return os.path.join(PathManager.get_logs_path(), f"{service_name}.log")

    @staticmethod
    def validate_path(path: str) -> bool:
        """Validate that a path is secure and within project"""
        try:
            normalized = PathManager.normalize_path(path)
            return (normalized.startswith(PathManager.get_project_root()) and 
                   PathManager._validate_path_safety(normalized))
        except Exception:
            return False

    @staticmethod
    def _validate_path_safety(path: str) -> bool:
        """Centralized validation of path safety"""
        try:
            normalized = os.path.normpath(path)
            return not any(part in ['..', '.'] for part in normalized.split(os.sep))
        except Exception:
            return False

    @staticmethod
    def ensure_directory(path: str) -> None:
        """Crée un dossier s'il n'existe pas"""
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def get_relative_path(path: str) -> str:
        """Retourne le chemin relatif par rapport à la racine du projet"""
        return os.path.relpath(path, PathManager.get_project_root())

    @staticmethod
    def join_paths(*paths: str) -> str:
        """Joint les chemins et normalise le résultat"""
        return PathManager.normalize_path(os.path.join(*paths))
