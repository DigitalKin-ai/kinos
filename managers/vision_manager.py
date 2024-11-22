import os
import json
import fnmatch
import subprocess
from typing import List, Dict, Optional
from utils.logger import Logger

class VisionManager:
    """
    Manager class for maintaining and providing repository structure visualization.
    Uses githubocto/repo-visualizer for generating interactive visualizations.
    """
    
    def _get_kinos_install_path(self) -> str:
        """Get the KinOS installation directory path."""
        # Get the directory containing the current script
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return current_dir

    def _get_repo_visualizer_path(self) -> str:
        """Get the repo-visualizer installation directory path."""
        kinos_path = self._get_kinos_install_path()
        return os.path.join(kinos_path, 'repo-visualizer')

    def __init__(self, 
                 output_file: str = "repo-visualizer.svg",
                 max_depth: int = 9,
                 file_colors: Optional[Dict[str, str]] = None):
        """
        Initialize the vision manager.
        Uses githubocto/repo-visualizer for generating interactive visualizations.
        
        Args:
            output_file (str): Path for output SVG file
            max_depth (int): Maximum folder depth to visualize
            file_colors (dict): Custom colors for file extensions
        """
        self.logger = Logger()
        self.map_path = output_file
        self.max_depth = max_depth
        self.file_colors = file_colors or {}
        
        # Default excluded paths
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

    def _get_file_size(self, filepath: str) -> int:
        """Get file size in bytes."""
        try:
            return os.path.getsize(filepath)
        except (OSError, IOError):
            return 0

    def _should_ignore(self, path: str, pattern: str) -> bool:
        """
        Check if a path matches an ignore pattern.
        
        Args:
            path (str): Path to check
            pattern (str): Glob pattern to match against
            
        Returns:
            bool: True if path should be ignored, False otherwise
        """
        try:
            # Handle directory-specific patterns
            if pattern.endswith('/'):
                if not os.path.isdir(path):
                    return False
                pattern = pattern[:-1]
                
            # Handle patterns starting with /
            if pattern.startswith('/'):
                pattern = pattern[1:]
                # Match only from root
                return fnmatch.fnmatch(path, pattern)
            else:
                # Match pattern against full path and any subpath
                path_parts = path.split(os.sep)
                return any(
                    fnmatch.fnmatch(os.path.join(*path_parts[i:]), pattern)
                    for i in range(len(path_parts))
                )
                
        except Exception as e:
            self.logger.warning(f"Error checking ignore pattern {pattern} for {path}: {str(e)}")
            return False


    async def update_map(self, root_path: str = "."):
        """Updates the repo visualization using repo-visualizer."""
        try:
            # Ensure node is available
            try:
                subprocess.run(['node', '--version'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                self.logger.error(
                    "\n❌ Node.js not found! Please install Node.js:\n"
                    "Download from https://nodejs.org/\n"
                    "\nAfter installing, restart your terminal/command prompt."
                )
                raise RuntimeError("Node.js not installed")

            # Get repo-visualizer path in KinOS installation directory
            repo_visualizer_path = self._get_repo_visualizer_path()

            # Check if repo-visualizer directory exists, if not clone it
            if not os.path.exists(repo_visualizer_path):
                self.logger.info("📦 Cloning repo-visualizer...")
                subprocess.run([
                    'git', 'clone', 'https://github.com/githubocto/repo-visualizer.git',
                    repo_visualizer_path  # Clone directly to KinOS directory
                ], check=True)
                self.logger.info(f"📦 Installing dependencies in {repo_visualizer_path}...")
                
                try:
                    # Vérifier la structure du projet
                    self.logger.debug("📂 Checking project structure...")
                    if os.path.exists(os.path.join(repo_visualizer_path, 'package.json')):
                        with open(os.path.join(repo_visualizer_path, 'package.json'), 'r') as f:
                            self.logger.debug(f"📄 package.json content: {f.read()}")
                    
                    # Create dist directory if it doesn't exist
                    dist_path = os.path.join(repo_visualizer_path, 'dist')
                    os.makedirs(dist_path, exist_ok=True)
                
                    # Update package.json build script
                    package_json_path = os.path.join(repo_visualizer_path, 'package.json')
                    with open(package_json_path, 'r') as f:
                        package_json = json.load(f)
                
                    # Update build script to output to dist directory
                    package_json['scripts'] = package_json.get('scripts', {})
                    package_json['scripts']['build'] = "node_modules/.bin/esbuild --target=es2019 ./src/index.jsx --bundle --platform=node --outfile=dist/index.js"
                
                    # Save updated package.json
                    with open(package_json_path, 'w') as f:
                        json.dump(package_json, f, indent=2)
                
                    # Run npm install and build
                    npm_path = 'npm'
                    self.logger.info("📦 Running npm install...")
                    install_result = subprocess.run(
                        [npm_path, 'install'], 
                        cwd=repo_visualizer_path, 
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    self.logger.debug(f"📦 npm install output: {install_result.stdout}")
                
                    # Build explicite du projet
                    self.logger.info("🔨 Running npm run build...")
                    build_result = subprocess.run(
                        [npm_path, 'run', 'build'], 
                        cwd=repo_visualizer_path, 
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    self.logger.debug(f"🔨 npm run build output: {build_result.stdout}")
                
                    # Verify build output
                    if not os.path.exists(os.path.join(dist_path, 'index.js')):
                        raise FileNotFoundError(f"Build failed: index.js not found in {dist_path}")
                    
                    self.logger.debug(f"📂 Contents of dist directory: {os.listdir(dist_path)}")
                        
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Failed to build repo-visualizer: {e.stderr}")
                    raise

            # Create visualization config
            config = {
                "output": self.map_path,
                "rootPath": root_path,
                "maxDepth": self.max_depth,
                "exclude": await self.get_ignored_files(),
                "colors": self.file_colors,
                "layout": "force",
                "direction": "LR",
                "linkDistance": 100,
                "linkStrength": 1,
                "charge": -100
            }

            # Save config
            config_path = os.path.join(os.path.dirname(self.map_path), "repo-visualizer.config.json")
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Log config contents
            self.logger.debug(f"Config file contents: {json.dumps(config, indent=2)}")

            # Run visualization using the local clone
            self.logger.debug("🎨 Generating repository visualization...")
            try:
                dist_path = os.path.join(self._get_repo_visualizer_path(), 'dist', 'index.js')
                
                # Verify index.js exists and has content
                if os.path.exists(dist_path):
                    file_size = os.path.getsize(dist_path)
                    self.logger.debug(f"index.js exists with size: {file_size} bytes")
                else:
                    raise FileNotFoundError(f"Built index.js not found at {dist_path}")

                # Verify config file location
                self.logger.debug(f"Config file exists: {os.path.exists(config_path)}")
                self.logger.debug(f"Config file location: {os.path.abspath(config_path)}")
                    
                result = subprocess.run([
                    'node',
                    dist_path,
                    '--config', config_path,
                    '--verbose'
                ], check=False, capture_output=True, text=True)
                
                # Log both stdout and stderr
                if result.stdout:
                    self.logger.debug(f"Command stdout: {result.stdout}")
                if result.stderr:
                    self.logger.debug(f"Command stderr: {result.stderr}")
                    
                # Check return code after logging
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(
                        result.returncode,
                        result.args,
                        output=result.stdout,
                        stderr=result.stderr
                    )
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Visualization command failed with return code {e.returncode}")
                if e.stdout:
                    self.logger.error(f"stdout: {e.stdout}")
                if e.stderr:
                    self.logger.error(f"stderr: {e.stderr}")
                raise
            except FileNotFoundError as e:
                self.logger.error(f"Build file not found: {str(e)}")
                raise

            self.logger.debug(f"✨ Repository map updated: {self.map_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to update repository map: {str(e)}")
            if isinstance(e, subprocess.CalledProcessError):
                self.logger.error(f"Command failed with output: {e.stderr}")
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

