import os
import subprocess
import asyncio
from utils.logger import Logger

class VisionManager:
    """Manager class for repository visualization using repo-visualizer."""
    
    def __init__(self):
        """Initialize the vision manager."""
        self.logger = Logger()

    async def generate_visualization(self):
        """
        Generate repository visualization using repo-visualizer.
        
        Raises:
            RuntimeError: If Node.js is not installed
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

            # Get repo-visualizer path
            repo_viz_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'repo-visualizer')
            dist_path = os.path.join(repo_viz_path, 'dist', 'index.js')

            if not os.path.exists(dist_path):
                raise FileNotFoundError(
                    f"repo-visualizer build not found at {dist_path}. "
                    "Please build repo-visualizer first."
                )

            # Run visualization with minimal options
            self.logger.debug("🎨 Generating repository visualization...")
            process = await asyncio.create_subprocess_exec(
                'node',
                dist_path,
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
                    f"node {dist_path} --verbose",
                    output=stdout,
                    stderr=stderr
                )

            self.logger.debug("✨ Repository visualization generated successfully")

        except Exception as e:
            self.logger.error(f"Failed to generate visualization: {str(e)}")
            raise

