import os
import subprocess
import asyncio
from typing import Dict
from utils.logger import Logger

class VisionManager:
    """Manager class for repository visualization using repo-visualizer."""
    
    def __init__(self):
        """Initialize the vision manager."""
        self.logger = Logger()
        self.config_path = "repo-visualizer.config.json"

    def _validate_repo_visualizer(self):
        """
        Validate that repo-visualizer is properly installed and configured.
        
        Raises:
            FileNotFoundError: If required files are missing
            ValueError: If configuration is invalid
        """
        # Get required paths
        repo_viz_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'repo-visualizer')
        dist_path = os.path.join(repo_viz_path, 'dist')
        index_js = os.path.join(dist_path, 'index.js')
        
        # Validate installation
        if not os.path.exists(repo_viz_path):
            raise FileNotFoundError(
                f"repo-visualizer not found at {repo_viz_path}. "
                "Please install it manually in the repo-visualizer directory."
            )
            
        if not os.path.exists(index_js):
            raise FileNotFoundError(
                f"repo-visualizer build not found at {index_js}. "
                "Please build repo-visualizer manually."
            )
            
        if not os.access(index_js, os.X_OK):
            raise ValueError(
                f"repo-visualizer build at {index_js} is not executable. "
                "Please check file permissions."
            )

    async def generate_visualization(self, root_path: str = "."):
        """
        Asynchronously generate repository visualization using repo-visualizer.
        
        Args:
            root_path (str): Root path to visualize
            
        Raises:
            RuntimeError: If Node.js is not installed
            FileNotFoundError: If repo-visualizer is not properly installed
            subprocess.CalledProcessError: If visualization generation fails
        """
        try:
            # Validate Node.js installation
            try:
                await asyncio.create_subprocess_exec('node', '--version')
            except FileNotFoundError:
                raise RuntimeError(
                    "Node.js not found! Please install Node.js from https://nodejs.org/"
                )

            # Validate repo-visualizer installation
            self._validate_repo_visualizer()

            # Get paths
            repo_viz_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'repo-visualizer')
            dist_path = os.path.join(repo_viz_path, 'dist', 'index.js')

            # Log config contents at debug level
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.logger.debug(f"Config file contents: {f.read()}")
            else:
                self.logger.warning(f"Config file not found at {self.config_path}")

            # Run visualization
            self.logger.debug("🎨 Generating repository visualization...")
            process = await asyncio.create_subprocess_exec(
                'node',
                dist_path,
                '--config', self.config_path,
                '--verbose',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                self.logger.error(f"Visualization command failed with return code {process.returncode}")
                if stdout:
                    self.logger.error(f"stdout: {stdout.decode()}")
                if stderr:
                    self.logger.error(f"stderr: {stderr.decode()}")
                raise subprocess.CalledProcessError(
                    process.returncode,
                    f"node {dist_path} --config {self.config_path} --verbose",
                    output=stdout,
                    stderr=stderr
                )

            self.logger.debug("✨ Repository visualization generated successfully")

        except Exception as e:
            self.logger.error(f"Failed to generate visualization: {str(e)}")
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

