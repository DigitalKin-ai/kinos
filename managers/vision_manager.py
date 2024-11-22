import os
from typing import List
import asyncio
import subprocess
from utils.logger import Logger

class VisionManager:
    """
    Manager class for maintaining and providing repository structure visualization.
    
    Responsible for:
    - Generating SVG visualization of repository structure
    - Tracking file system changes
    - Providing visual context to agents
    - Managing visualization updates
    
    Attributes:
        logger (Logger): Logging utility instance
        map_path (str): Path to SVG map file
        _last_update (float): Timestamp of last map update
    """
    
    def __init__(self):
        """Initialize the vision manager with required components."""
        self.logger = Logger()
        self.map_path = "repo-map.svg"
        self._last_update = 0
        
    async def get_ignored_files(self) -> List[str]:
        """
        Get list of files to ignore in visualization.
        
        Combines patterns from .gitignore with default .aider* pattern.
        
        Returns:
            List[str]: List of ignore patterns
            
        Note:
            Always includes .aider* pattern regardless of .gitignore contents
        """
        # Start with default patterns
        ignored = [".aider*"]
        
        # Add patterns from .gitignore if it exists
        if os.path.exists(".gitignore"):
            try:
                with open(".gitignore", "r", encoding="utf-8") as f:
                    # Add each non-empty, non-comment line
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            ignored.append(line)
            except Exception as e:
                self.logger.warning(f"⚠️ Error reading .gitignore: {str(e)}")
        
        return ignored

    async def update_map(self) -> bool:
        """
        Update repository visualization if needed.
        
        Checks for file system changes since last update and regenerates
        the SVG map if necessary using repo-visualizer.
        
        Returns:
            bool: True if map was updated, False if no update was needed
            
        Raises:
            subprocess.CalledProcessError: If repo-visualizer execution fails
            OSError: If there are file system access issues
        """
        pass

    async def get_map(self) -> str:
        """
        Get current repository visualization.
        
        Returns the SVG content of the current repository map.
        Updates the map first if it doesn't exist.
        
        Returns:
            str: SVG content of repository map
            
        Raises:
            FileNotFoundError: If map file doesn't exist and can't be generated
            OSError: If there are file access issues
        """
        pass

    def _has_changes(self) -> bool:
        """
        Check if repository has changed since last map update.
        
        Compares file modification times against last update timestamp.
        
        Returns:
            bool: True if files have been modified, False otherwise
        """
        # If no previous update, consider it changed
        if not self._last_update:
            return True
            
        try:
            # Walk through repository
            for root, _, files in os.walk("."):
                # Skip ignored directories
                if any(p in root for p in [".git", "__pycache__", "node_modules"]):
                    continue
                    
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # Check if file was modified after last update
                        if os.path.getmtime(file_path) > self._last_update:
                            return True
                    except OSError:
                        continue  # Skip files we can't access
                        
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking for changes: {str(e)}")
            return True  # Assume changes on error to be safe

    async def _generate_map(self) -> None:
        """
        Generate repository visualization using repo-visualizer.
        
        Executes repo-visualizer with current ignore patterns to create
        new SVG map.
        
        Raises:
            subprocess.CalledProcessError: If repo-visualizer execution fails
            OSError: If there are file system access issues
        """
        pass
