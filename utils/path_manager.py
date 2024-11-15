import os
import re
import json
import traceback
import platform
import shutil
from typing import Optional, Dict, Any, List

class PathManager:
    """Centralized and secure path management for KinOS"""
    
    _CONFIG_FILE = 'config/missions.json'
    _DEFAULT_MISSIONS_DIR = os.path.expanduser('~/KinOS_Missions')
    
    @classmethod
    def get_project_root(cls) -> str:
        """Returns the current working directory as project root"""
        return os.getcwd()

    @classmethod
    def get_mission_path(cls, mission_name: str = None) -> str:
        """Get mission path, defaulting to current directory"""
        return os.getcwd()

    @classmethod
    def get_kinos_root(cls) -> str:
        """Returns the KinOS installation directory"""
        # Le fichier path_manager.py est dans utils/, donc remonter de 2 niveaux
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @classmethod
    def get_team_types_root(cls) -> str:
        """Get the team types configuration directory"""
        return os.path.join(cls.get_kinos_root(), "team_types")

    @staticmethod
    def get_config_path() -> str:
        """Retourne le chemin vers le dossier de configuration"""
        return os.path.join(PathManager.get_project_root(), "config")

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
    def validate_mission_path(cls, path: str, strict: bool = False) -> bool:
        """
        Comprehensive mission path validation
        
        Args:
            path (str): Path to validate
            strict (bool): Enable stricter validation checks
        
        Returns:
            bool: Whether path is valid for mission use
        """
        try:
            # Ensure absolute path
            if not os.path.isabs(path):
                return False
            
            # Check path exists or is creatable
            try:
                os.makedirs(path, exist_ok=True)
            except (PermissionError, OSError):
                return False
            
            # Check read and write permissions
            if not os.access(path, os.R_OK | os.W_OK):
                return False
            
            # Optional strict checks
            if strict:
                # Prevent use of system directories
                system_dirs = ['/sys', '/proc', '/dev', '/etc']
                if any(path.startswith(sys_dir) for sys_dir in system_dirs):
                    return False
                
                # Check free disk space (minimum 100MB)
                try:
                    total, used, free = shutil.disk_usage(path)
                    if free < 100 * 1024 * 1024:  # 100MB in bytes
                        return False
                except Exception:
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
    def get_config_path() -> str:
        """Retourne le chemin vers le dossier de configuration"""
        return os.path.join(PathManager.get_project_root(), "config")


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
    def get_cache_file_path(cache_key: str) -> str:
        """Retourne le chemin vers un fichier de cache"""
        cache_dir = os.path.join(PathManager.get_temp_path(), "cache")
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, f"{cache_key}.cache")

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize a file path"""
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

    @classmethod
    def get_prompt_file(cls, agent_name: str, team_id: Optional[str] = None) -> Optional[str]:
        """
        Get prompt file path for an agent
        
        Args:
            agent_name: Name of the agent
            team_id: Optional team ID to narrow search
        
        Returns:
            str: Path to the prompt file, or None if not found
        """
        try:
            # If team_id is provided, search in that team's directory first
            if team_id:
                # Try both teams and team_types directories
                search_dirs = [
                    os.path.join(cls.get_kinos_root(), "teams", team_id),
                    os.path.join(cls.get_team_types_root(), f"team_{team_id}")
                ]
                
                prompt_filename_options = [
                    f"{agent_name.lower()}.md",
                    f"{agent_name}.md",
                    f"{agent_name.lower()}_prompt.md",
                    f"{agent_name}_prompt.md"
                ]
                
                for search_dir in search_dirs:
                    if os.path.exists(search_dir):
                        for filename in prompt_filename_options:
                            prompt_path = os.path.join(search_dir, filename)
                            if os.path.exists(prompt_path):
                                return prompt_path
            
            # If no team_id or file not found, search in all team directories
            for base_dir in ["teams", "team_types"]:
                search_root = os.path.join(cls.get_kinos_root(), base_dir)
                
                if os.path.exists(search_root):
                    for team_folder in os.listdir(search_root):
                        team_dir = os.path.join(search_root, team_folder)
                        if not os.path.isdir(team_dir):
                            continue
                            
                        for filename in prompt_filename_options:
                            prompt_path = os.path.join(team_dir, filename)
                            if os.path.exists(prompt_path):
                                return prompt_path
            
            return None
            
        except Exception as e:
            print(f"Error getting prompt file: {str(e)}")
            return None

    @classmethod
    def get_prompt_path(cls, agent_name: str, team_id: Optional[str] = None) -> Optional[str]:
        """
        Get prompt file path for an agent
        
        Args:
            agent_name: Name of the agent
            team_id: Optional team ID to narrow search
        
        Returns:
            str: Path to the prompt file, or None if not found
        """
        return cls.get_prompt_file(agent_name, team_id)

    @staticmethod
    def get_log_file(service_name: str) -> str:
        """Retourne le chemin vers un fichier de log spécifique"""
        return os.path.join(PathManager.get_logs_path(), f"{service_name}.log")

    @staticmethod
    def get_chats_path(mission_name: Optional[str] = None) -> str:
        """
        Returns the path to the chats directory, optionally for a specific mission
        
        Args:
            mission_name (Optional[str]): Name of the mission to get chats for
        
        Returns:
            str: Path to the chats directory
        """
        chats_dir = os.path.join(PathManager.get_project_root(), "chats")
        
        # Create base chats directory if it doesn't exist
        os.makedirs(chats_dir, exist_ok=True)
        
        # If mission name is provided, create a subdirectory for that mission
        if mission_name:
            # Normalize mission name for filesystem use
            normalized_mission_name = mission_name.lower().replace(' ', '_').replace('-', '_')
            mission_chats_dir = os.path.join(chats_dir, normalized_mission_name)
            os.makedirs(mission_chats_dir, exist_ok=True)
            return mission_chats_dir
        
        return chats_dir

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

    @staticmethod
    def validate_agent_name(name: str) -> bool:
        """
        Validate agent name format.
        Only allows letters, numbers, underscore, and hyphen.
        """
        if not name:
            return False
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))
