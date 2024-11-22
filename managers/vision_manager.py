import os
from typing import List
from repo_visualizer import render_repository_graph
from utils.logger import Logger

class VisionManager:
    """
    Manager class for maintaining and providing repository structure visualization.
    
    Responsible for:
    - Generating SVG visualization of repository structure
    - Providing visual context to agents
    - Managing visualization updates
    """
    
    def __init__(self):
        """Initialize the vision manager."""
        self.logger = Logger()
        self.map_path = "repo-map.svg"
        
    async def get_ignored_files(self) -> List[str]:
        """
        Gets list of ignored files by:
        1. Reading all patterns from .gitignore
        2. Adding .aider* pattern
        
        Returns:
            List[str]: List of ignore patterns
        """
        ignored = [".aider*"]
        if os.path.exists(".gitignore"):
            try:
                with open(".gitignore", "r", encoding="utf-8") as f:
                    ignored.extend(line.strip() for line in f 
                                 if line.strip() and not line.startswith("#"))
            except Exception as e:
                self.logger.warning(f"⚠️ Error reading .gitignore: {str(e)}")
        return ignored

    async def update_map(self):
        """
        Updates the repo map SVG using repo-visualizer.
        Called after Aider operations that modify files.
        
        Raises:
            Exception: If repo-visualizer rendering fails
            OSError: If there are file system access issues
        """
        try:
            # Get ignore patterns
            ignored = await self.get_ignored_files()
            
            # Generate SVG using repo-visualizer
            self.logger.debug("Generating repository visualization...")
            svg_content = render_repository_graph(
                root_path=".",  # Current directory
                output_file=self.map_path,
                excluded_globs=ignored
            )
            
            # Save the SVG
            with open(self.map_path, "w", encoding="utf-8") as f:
                f.write(svg_content)
                
            self.logger.debug(f"✨ Repository map updated: {self.map_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to update repository map: {str(e)}")
            raise

    async def get_map(self) -> str:
        """
        Returns the current repo map SVG content.
        Used by agents when they need visual context.
        
        Returns:
            str: SVG content of repository map
            
        Raises:
            FileNotFoundError: If map file doesn't exist and can't be generated
            OSError: If there are file access issues
        """
        try:
            # Create map if it doesn't exist
            if not os.path.exists(self.map_path):
                self.logger.debug("Repository map not found, generating...")
                await self.update_map()
            
            # Read and return SVG content
            with open(self.map_path, "r", encoding="utf-8") as f:
                return f.read()
                
        except Exception as e:
            self.logger.error(f"Failed to get repository map: {str(e)}")
            raise

