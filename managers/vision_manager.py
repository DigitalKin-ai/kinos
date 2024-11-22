import os
from typing import List, Dict, Optional
from repo_visualizer import render_repository_graph
from utils.logger import Logger

class VisionManager:
    """
    Manager class for maintaining and providing repository structure visualization.
    
    Uses repo-visualizer v0.7.1 to generate SVG visualizations of repository structure.
    """
    
    def __init__(self, 
                 output_file: str = "repo-map.svg",
                 max_depth: int = 9,
                 file_colors: Optional[Dict[str, str]] = None):
        """
        Initialize the vision manager.
        
        Args:
            output_file (str): Path for output SVG file
            max_depth (int): Maximum folder depth to visualize
            file_colors (dict): Custom colors for file extensions
        """
        self.logger = Logger()
        self.map_path = output_file
        self.max_depth = max_depth
        self.file_colors = file_colors or {}
        
        # Default excluded paths for repo-visualizer
        self.default_excluded = [
            "node_modules",
            "bower_components",
            "dist",
            "out", 
            "build",
            "eject",
            ".next",
            ".netlify",
            ".yarn",
            ".vscode",
            ".git",
            "__pycache__",
            "*.pyc",
            "package-lock.json",
            "yarn.lock"
        ]
        
    async def get_ignored_files(self) -> List[str]:
        """Gets list of ignored files and default exclusions."""
        ignored = self.default_excluded.copy()
        
        # Add .aider* pattern
        ignored.append(".aider*")
        
        # Add patterns from .gitignore
        if os.path.exists(".gitignore"):
            try:
                with open(".gitignore", "r", encoding="utf-8") as f:
                    ignored.extend(line.strip() for line in f 
                                 if line.strip() and not line.startswith("#"))
            except Exception as e:
                self.logger.warning(f"⚠️ Error reading .gitignore: {str(e)}")
                
        return ignored

    async def update_map(self, root_path: str = "."):
        """
        Updates the repo map SVG using repo-visualizer.
        
        Args:
            root_path (str): Root directory to visualize
            
        Raises:
            Exception: If visualization fails
            OSError: If there are file system issues
        """
        try:
            # Get ignore patterns
            excluded_paths = await self.get_ignored_files()
            
            # Convert excluded paths to glob patterns
            excluded_globs = [f"**/{path}/**" for path in excluded_paths]
            excluded_globs.extend([
                "**/*.{png,jpg,jpeg,gif,ico,svg}",  # Exclude images
                "**/*.{pyc,pyo,pyd}",  # Exclude Python bytecode
                "**/__pycache__/**"     # Exclude Python cache
            ])
            
            self.logger.debug("Generating repository visualization...")
            
            # Generate SVG using repo-visualizer v0.7.1 with correct options
            svg_content = render_repository_graph(
                root_path=root_path,
                output_file=self.map_path,
                excluded_paths=excluded_paths,  # List of paths, not comma-separated
                excluded_globs=excluded_globs,  # List of globs, not semicolon-separated
                max_depth=self.max_depth,
                colors=self.file_colors  # Parameter is 'colors' not 'file_colors'
            )
            
            # Save the SVG
            with open(self.map_path, "w", encoding="utf-8") as f:
                f.write(svg_content)
                
            self.logger.debug(f"✨ Repository map updated: {self.map_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to update repository map: {str(e)}")
            raise

    async def get_map(self, force_update: bool = False) -> str:
        """
        Returns the current repo map SVG content.
        
        Args:
            force_update (bool): Force map regeneration
            
        Returns:
            str: SVG content of repository map
            
        Raises:
            FileNotFoundError: If map doesn't exist and can't be generated
            OSError: If there are file access issues
        """
        try:
            if force_update or not os.path.exists(self.map_path):
                self.logger.debug(
                    "Repository map not found or update forced, generating..."
                )
                await self.update_map()
            
            with open(self.map_path, "r", encoding="utf-8") as f:
                return f.read()
                
        except Exception as e:
            self.logger.error(f"Failed to get repository map: {str(e)}")
            raise

    def set_file_colors(self, colors: Dict[str, str]):
        """
        Update custom colors for file extensions.
        
        Args:
            colors (dict): Mapping of file extensions to colors
        """
        self.file_colors.update(colors)

