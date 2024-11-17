import os
import re
import json
import traceback
import platform
import shutil
from typing import Optional, Dict, Any, Union, List
from datetime import datetime

class PathManager:
    @classmethod
    def _log(cls, message: str, level: str = 'info'):
        """Simple internal logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level.upper()}] {message}")
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
            # Validate inputs
            if not agent_name:
                raise ValueError("Agent name is required")
                
            # If no team_name specified, use default
            if not team_name:
                team_name = 'default'

            # Ensure team name has prefix
            team_dir_name = f"team_{team_name}" if not team_name.startswith("team_") else team_name
            
            # Build prompt path
            prompts_dir = os.path.join(os.getcwd(), team_dir_name, "prompts")
            os.makedirs(prompts_dir, exist_ok=True)
            
            # Define default prompts for different agent types
            default_prompts = {
                'demande': """# Mission Request Agent

You are the Mission Request agent responsible for managing and clarifying mission requirements.
Your role is to:
1. Review and maintain demande.md
2. Ensure mission objectives are clear
3. Track and update mission progress

## Guidelines
- Keep mission requirements up to date
- Break down complex requirements
- Track completion status
- Flag any unclear points

## Format
Always structure your responses as:
1. What aspect of the mission you're addressing
2. Why it needs attention
3. How you'll improve it

## Rules
- Focus on demande.md
- Keep requirements clear and specific
- Update status regularly
- Flag blockers and dependencies""",

                'documentaliste': """# Documentation Agent

You are the Documentation agent responsible for maintaining project documentation.
Your role is to:
1. Keep documentation up to date
2. Ensure clarity and completeness
3. Maintain consistent structure

## Guidelines
- Update docs as code changes
- Keep format consistent
- Add examples where helpful
- Cross-reference related docs

## Format
Always structure your responses as:
1. What documentation needs updating
2. Why the update is needed
3. How you'll improve it

## Rules
- Focus on clarity
- Keep docs current
- Use consistent formatting
- Add helpful examples""",

                'validation': """# Validation Agent

You are the Validation agent responsible for quality control and testing.
Your role is to:
1. Verify implementation matches requirements
2. Check for consistency
3. Flag potential issues

## Guidelines
- Review changes against requirements
- Check for inconsistencies
- Validate functionality
- Report issues clearly

## Format
Always structure your responses as:
1. What you're validating
2. Why it needs checking
3. How you'll verify it

## Rules
- Be thorough
- Document findings
- Flag all issues
- Suggest improvements""",

                'chroniqueur': """# Project Chronicler Agent

You are the Project Chronicler responsible for tracking project history and progress.
Your role is to:
1. Document project evolution
2. Track key decisions
3. Maintain project timeline

## Guidelines
- Record significant changes
- Document decision rationale
- Keep history organized
- Highlight milestones

## Format
Always structure your responses as:
1. What you're documenting
2. Why it's significant
3. How you'll record it

## Rules
- Be comprehensive
- Stay objective
- Link related events
- Track key decisions"""
            }

            # Get default prompt for agent type
            agent_type = agent_name.lower()
            default_prompt = default_prompts.get(agent_type, default_prompts.get('demande'))
            
            # Create prompt file path
            prompt_path = os.path.join(prompts_dir, f"{agent_name}.md")
            
            # If prompt doesn't exist or is empty, write default
            if not os.path.exists(prompt_path) or os.path.getsize(prompt_path) == 0:
                with open(prompt_path, 'w', encoding='utf-8') as f:
                    f.write(default_prompt)
                    from utils.logger import Logger
                    logger = Logger()
                    logger.log(f"Created default prompt for {agent_name} in {team_dir_name}", 'info')
                
            return prompt_path
                
        except Exception as e:
            from utils.logger import Logger
            logger = Logger()
            logger.log(f"Error getting prompt file: {str(e)}", 'error')
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
        try:
            # Remove any existing team_ prefix and clean name
            team_name = name.replace('team_', '').strip()
            
            # Create team folder name with single prefix
            team_folder = f"team_{team_name}"
            
            # Get absolute path, ensuring we don't nest team folders
            base_dir = os.getcwd()
            if "team_" in base_dir:
                # Already in a team directory, use parent
                base_dir = os.path.dirname(base_dir)
                
            team_path = os.path.abspath(os.path.join(base_dir, team_folder))
            
            # Ensure directory exists
            os.makedirs(team_path, exist_ok=True)
            
            return team_path
            
        except Exception as e:
            cls._log(f"Error getting team path: {str(e)}", 'error')
            return os.path.join(os.getcwd(), f"team_{name}")

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
                if not team_dirs:
                    cls._log("No teams found in mission directory", 'warning')
            except:
                # Fallback to print if logger not available
                if team_dirs:
                    logger = Logger()
                else:
                    print("No teams found in mission directory")
            
            return team_dirs
        
        except Exception as e:
            # Fallback error handling
            try:
                cls._log(f"Error listing teams: {str(e)}", 'error')
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
