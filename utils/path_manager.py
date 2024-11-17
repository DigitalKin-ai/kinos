import os
import re
import json
import traceback
import platform
import shutil
from typing import Optional, Dict, Any, Union, List

class PathManager:
    """Centralized and secure path management for KinOS"""
    
    _CONFIG_FILE = 'config/missions.json'
    _DEFAULT_MISSIONS_DIR = os.path.expanduser('~/KinOS_Missions')
    
    @classmethod
    def get_project_root(cls) -> str:
        """Returns the current team directory"""
        current_dir = os.getcwd()
        team_dir = next((d for d in os.listdir(current_dir) if d.startswith('team_')), current_dir)
        return os.path.join(current_dir, team_dir)

    @classmethod
    def get_mission_path(cls, mission_name: str = None) -> str:
        """Get mission path within current team directory"""
        return cls.get_project_root()

    @classmethod
    def get_kinos_root(cls) -> str:
        """Returns the current working directory"""
        return os.getcwd()


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
    def get_prompt_file(cls, agent_name: str, team_name: Optional[str] = None) -> Optional[str]:
        """Get prompt file path for an agent in the team's prompts directory"""
        try:
            # Get current team directory
            current_dir = os.getcwd()
            
            # Get active team from TeamService
            try:
                from services import init_services
                services = init_services(None)
                team_service = services['team_service']
                active_team = team_service.get_active_team()
                if active_team:
                    team_name = active_team.get('name')
            except Exception as e:
                from utils.logger import Logger
                logger = Logger()
                logger.log(f"Error getting active team: {str(e)}", 'warning')

            # If no team_name specified or found, raise error
            if not team_name:
                raise ValueError("No active team found")

            # Construct team directory path
            team_dir = os.path.join(current_dir, f"team_{team_name}")
            
            # Look for prompt file in team's prompts directory
            prompts_dir = os.path.join(team_dir, "prompts")
            os.makedirs(prompts_dir, exist_ok=True)

            # Try normalized and original agent name
            for filename in [f"{agent_name.lower()}.md", f"{agent_name}.md"]:
                prompt_path = os.path.join(prompts_dir, filename)
                if os.path.exists(prompt_path):
                    return prompt_path

            return None

        except Exception as e:
            from utils.logger import Logger
            logger = Logger()
            logger.log(f"Error finding prompt file: {str(e)}", 'error')
            return None

    @classmethod
    def get_prompt_path(cls, agent_name: str, team_name: Optional[str] = None) -> Optional[str]:
        """
        Get prompt file path for an agent
        
        Args:
            agent_name: Name of the agent
            team_name: Optional team name to narrow search
        
        Returns:
            str: Path to the prompt file, or None if not found
        """
        return cls.get_prompt_file(agent_name, team_name)

    @classmethod
    def get_team_path(cls, name: str) -> str:
        """Get the path for a team"""
        team_folder = f"team_{name}" if not name.startswith('team_') else name
        team_path = os.path.join(os.getcwd(), team_folder)
        os.makedirs(team_path, exist_ok=True)
        return team_path

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
    def get_chat_history_path(team_name: Optional[str] = None, agent_name: Optional[str] = None) -> str:
        """
        Get the path for chat history files
        
        Args:
            team_name: Team name
            agent_name: Name of the agent
        
        Returns:
            str: Path to chat history directory or file
        """
        try:
            # If no team_name, try to get active team
            if not team_name:
                from services import init_services
                services = init_services(None)
                team_service = services['team_service']
                active_team = team_service.get_active_team()
                team_name = active_team.get('name') if active_team else 'default'
            
            # Normalize team folder name
            team_folder = f"team_{team_name}" if not team_name.startswith('team_') else team_name
            
            # Create full path
            chat_history_dir = os.path.join(os.getcwd(), team_folder, "history")
            
            # Create directory if it doesn't exist
            os.makedirs(chat_history_dir, exist_ok=True)
            
            # If agent name is provided, create agent-specific chat history file path
            if agent_name:
                chat_history_file = f".kinos.{agent_name}.chat.history.md"
                return os.path.join(chat_history_dir, chat_history_file)
            
            return chat_history_dir
            
        except Exception as e:
            print(f"Error getting chat history path: {str(e)}")
            return os.path.join(os.getcwd(), "history")

    @classmethod
    def list_teams(cls) -> List[str]:
        """
        List team directories in current working directory
        
        Returns:
            List of team names (without 'team_' prefix)
        """
        try:
            # Get the mission directory
            mission_dir = os.getcwd()
            
            # List all directories in the mission directory
            all_dirs = [d for d in os.listdir(mission_dir) if os.path.isdir(os.path.join(mission_dir, d))]
            
            # Filter directories that start with "team_" and remove None values
            team_dirs = [d[5:] for d in all_dirs if d.startswith("team_") and d[5:]]
            
            # Optional: use logger if available
            try:
                from utils.logger import Logger
                logger = Logger()
                if team_dirs:
                    logger.log(f"Found teams: {', '.join(team_dirs)}", 'info')
                else:
                    logger.log("No teams found in mission directory", 'warning')
            except:
                # Fallback to print if logger not available
                if team_dirs:
                    print(f"Found teams: {', '.join(team_dirs)}")
                else:
                    print("No teams found in mission directory")
            
            return team_dirs
        
        except Exception as e:
            # Fallback error handling
            try:
                from utils.logger import Logger
                logger = Logger()
                logger.log(f"Error listing teams: {str(e)}", 'error')
            except:
                print(f"Error listing teams: {str(e)}")
            
            return []

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
