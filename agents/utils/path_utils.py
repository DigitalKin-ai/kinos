"""
Path management utilities
"""
import os
from typing import List

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
    def normalize_path(path: str) -> str:
        """Normalize a file path"""
        return os.path.normpath(os.path.abspath(path))
