"""
Path management utilities
"""
import os
from typing import List, Optional

def validate_paths(mission_dir: str) -> bool:
    """
    Validate mission directory path
    
    Args:
        mission_dir: Mission directory path
        
    Returns:
        bool: True if path is valid
    """
    try:
        # Check existence
        if not os.path.exists(mission_dir):
            return False
            
        # Check permissions
        if not os.access(mission_dir, os.R_OK | os.W_OK):
            return False
            
        # Check is directory
        if not os.path.isdir(mission_dir):
            return False
            
        return True
        
    except Exception:
        return False
        
def get_relative_path(file_path: str, base_path: str) -> str:
    """
    Get path relative to base path
    
    Args:
        file_path: Full file path
        base_path: Base path to make relative to
        
    Returns:
        str: Relative path
    """
    try:
        return os.path.relpath(file_path, base_path)
    except ValueError:
        return file_path

# Add a simple PathManager
class PathManager:
    @staticmethod
    def get_project_root() -> str:
        """Get the project root directory"""
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    @staticmethod
    def get_kinos_root() -> str:
        """Get the KinOS root directory"""
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    @staticmethod
    def get_team_types_root() -> str:
        """Get the team types configuration directory"""
        return os.path.join(PathManager.get_kinos_root(), "team_types")

    @staticmethod
    def get_teams_root() -> str:
        """Get the runtime teams working directory"""
        return os.path.join(os.getcwd(), "teams")
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize a file path"""
        return os.path.normpath(os.path.abspath(path))

    @staticmethod
    def get_agent_prompt_path(team_id: str, agent_name: str) -> Optional[str]:
        """
        Get prompt file path for an agent in a team
        
        Args:
            team_id: ID of the team
            agent_name: Name of the agent
        
        Returns:
            str: Path to the prompt file, or None if not found
        """
        try:
            # Construct path to team's prompts directory
            team_prompts_dir = os.path.join(PathManager.get_kinos_root(), "teams", team_id)
            
            # Try different filename variations
            prompt_filename_options = [
                f"{agent_name.lower()}.md",
                f"{agent_name}.md",
                f"{agent_name.lower()}_prompt.md",
                f"{agent_name}_prompt.md"
            ]
            
            for filename in prompt_filename_options:
                prompt_path = os.path.join(team_prompts_dir, filename)
                if os.path.exists(prompt_path):
                    return prompt_path
            
            return None
            
        except Exception as e:
            print(f"Error getting agent prompt path: {str(e)}")
            return None
