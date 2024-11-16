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
    def get_prompt_file(cls, agent_name: str, team_id: Optional[Union[str, Dict[str, Any]]] = None, team_name: Optional[str] = None) -> Optional[str]:
        """
        Get prompt file path for an agent with comprehensive logging and error handling
        
        Args:
            agent_name: Name of the agent
            team_id: Optional team ID to narrow search (can be string or dict)
            team_name: Optional team name for logging context
        
        Returns:
            str: Path to the prompt file, or None if not found
        """
        # Get team service to find the team if not provided
        if not team_id:
            try:
                from services import init_services
                services = init_services(None)
                team_service = services['team_service']
                
                # Find team containing this agent
                for team in team_service.team_types:
                    if isinstance(team, dict):
                        team_agents = team.get('agents', [])
                        for agent in team_agents:
                            agent_name_to_check = agent.get('name', agent) if isinstance(agent, dict) else agent
                            if agent_name == agent_name_to_check:
                                team_id = team.get('id')
                                team_name = team.get('name')
                                break
                        if team_id:
                            break

            except Exception as e:
                print(f"Error finding team for agent {agent_name}: {str(e)}")

        # Normalize team folder name
        team_folder = None
        if isinstance(team_id, dict):
            team_name = team_id.get('name', team_name)
            team_folder = team_id.get('id', '').replace('team_', '')
        elif team_id:
            team_folder = str(team_id).replace('team_', '')
            
        # Get logging context using team name
        log_context = f"[{team_name or team_folder or 'unknown_team'}]"
        
        try:
            # If no team specified, select a random team
            if not team_folder:
                try:
                    # List available team folders directly
                    team_types_dir = cls.get_team_types_root()
                    available_teams = [d for d in os.listdir(team_types_dir) 
                                     if os.path.isdir(os.path.join(team_types_dir, d))]
                    
                    if not available_teams:
                        print(f"{log_context} ERROR: No team folders found")
                        return None
                    
                    # Select random team folder
                    import random
                    team_folder = random.choice(available_teams)
                    team_name = team_folder.replace('_', ' ').title()
                    
                    # Update logging context
                    log_context = f"[{team_name}]"
                    print(f"{log_context} Selected team folder: {team_folder}")
                    
                except Exception as e:
                    print(f"{log_context} ERROR: Could not select team folder: {str(e)}")
                    return None

            print(f"{log_context} DEBUG: Searching for prompt file for agent: {agent_name}")
            print(f"{log_context} DEBUG: Team folder: {team_folder}")

            # Normalize agent name for matching
            normalized_agent_name = agent_name.lower()

            # Define prompt filename options
            prompt_filename_options = [
                f"{normalized_agent_name}.md",
                f"{agent_name}.md"  # Also try original case
            ]

            # Search directories with priority using folder names
            search_directories = []
            
            # Add team-specific directories if team folder exists
            if team_folder:
                search_directories.extend([
                    os.path.join(cls.get_project_root(), team_folder),  # Current mission team dir
                    os.path.join(cls.get_team_types_root(), team_folder)  # Team types dir
                ])
            
            # Add fallback search paths
            search_directories.extend([
                os.path.join(cls.get_team_types_root(), "default"),  # Default prompts
                cls.get_team_types_root()  # Root prompts dir
            ])
            
            # Remove duplicate and None values
            search_directories = list(dict.fromkeys(d for d in search_directories if d is not None))
            
            # Comprehensive search
            matched_paths = []
            for search_dir in search_directories:
                if not os.path.exists(search_dir):
                    #print(f"{log_context} DEBUG: Skipping non-existent directory: {search_dir}")
                    continue
                
                try:
                    # Search through all subdirectories
                    for root, _, files in os.walk(search_dir):
                        for filename in prompt_filename_options:
                            prompt_path = os.path.join(root, filename)
                            if os.path.exists(prompt_path):
                                #print(f"{log_context} DEBUG: Found potential prompt file: {prompt_path}")
                                matched_paths.append(prompt_path)
                
                except PermissionError:
                    print(f"{log_context} WARNING: Permission denied accessing {search_dir}")
                except Exception as search_error:
                    print(f"{log_context} ERROR: Error searching directory {search_dir}: {str(search_error)}")
            
            # Select best match
            if matched_paths:
                # Prioritize exact matches
                exact_match_paths = [
                    path for path in matched_paths 
                    if os.path.splitext(os.path.basename(path))[0].lower() == normalized_agent_name
                ]
                
                # If exact matches exist, use the first one
                if exact_match_paths:
                    selected_path = exact_match_paths[0]
                    print(f"{log_context} DEBUG: Selected exact match prompt file: {selected_path}")
                    return selected_path
                
                # If no exact match, use the first found path
                selected_path = matched_paths[0]
                print(f"{log_context} DEBUG: Selected first found prompt file: {selected_path}")
                return selected_path
            
            # No prompt file found
            print(f"{log_context} WARNING: No prompt file found for agent {agent_name}")
            return None
        
        except Exception as e:
            print(f"{log_context} CRITICAL ERROR in get_prompt_file: {str(e)}")
            print(f"{log_context} Traceback: {traceback.format_exc()}")
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
    def get_team_path(team_id: Optional[str] = None, team_name: Optional[str] = None) -> str:
        """
        Get the path for a specific team with comprehensive logging and error handling
        
        Args:
            team_id: Optional team identifier (folder name)
            team_name: Optional team name for logging context
        
        Returns:
            str: Path to the team directory
        """
        # Use the team_id directly as the folder name, without adding "team_" prefix
        team_folder = team_id if team_id else ""
        return os.path.join(PathManager.get_project_root(), team_folder)

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

    @classmethod
    def list_teams(cls) -> List[str]:
        """
        List all teams in the mission directory
        
        Returns:
            List of team names
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
