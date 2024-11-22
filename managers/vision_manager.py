import os
from typing import List, Dict, Optional
import graphviz
from utils.logger import Logger

class VisionManager:
    """
    Manager class for maintaining and providing repository structure visualization.
    Uses graphviz to generate SVG visualizations of repository structure with size-proportional nodes.
    """
    
    def __init__(self, 
                 output_file: str = "repo-map.svg",
                 max_depth: int = 9,
                 file_colors: Optional[Dict[str, str]] = None,
                 min_size: float = 0.5,
                 max_size: float = 4.0):
        """
        Initialize the vision manager.
        
        Args:
            output_file (str): Path for output SVG file
            max_depth (int): Maximum folder depth to visualize
            file_colors (dict): Custom colors for file extensions
            min_size (float): Minimum node size in inches
            max_size (float): Maximum node size in inches
        """
        self.logger = Logger()
        self.map_path = output_file
        self.max_depth = max_depth
        self.file_colors = file_colors or {}
        self.min_size = min_size
        self.max_size = max_size
        
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

    def _calculate_node_size(self, file_size: int) -> float:
        """
        Calculate node size based on file size with logarithmic scaling.
        
        Args:
            file_size (int): Size of file in bytes
            
        Returns:
            float: Node size in inches between min_size and max_size
        """
        if file_size == 0:
            return self.min_size
            
        import math
        # Use log scaling to handle wide range of file sizes
        log_size = math.log(file_size + 1, 10)  # +1 to handle empty files
        max_log_size = math.log(1024 * 1024 * 100, 10)  # 100MB max for scaling
        
        # Scale between min and max size
        scale = (log_size / max_log_size)
        size = self.min_size + (self.max_size - self.min_size) * scale
        
        return min(max(size, self.min_size), self.max_size)

    async def update_map(self, root_path: str = "."):
        """
        Updates the repo map SVG using graphviz.
        
        Args:
            root_path (str): Root directory to visualize
        """
        try:
            # Create new directed graph
            dot = graphviz.Digraph(
                'repo_structure',
                node_attr={'style': 'filled', 'fontname': 'Arial'},
                edge_attr={'fontname': 'Arial'},
                engine='dot'
            )
            
            # Get ignore patterns
            ignored_paths = await self.get_ignored_files()
            
            # Track processed paths to handle symlinks
            processed = set()
            
            def add_path_to_graph(path: str, parent: Optional[str] = None, depth: int = 0):
                """Recursively add paths to graph."""
                if depth > self.max_depth:
                    return
                    
                rel_path = os.path.relpath(path, root_path)
                if any(self._should_ignore(rel_path, pattern) for pattern in ignored_paths):
                    return
                    
                abs_path = os.path.abspath(path)
                if abs_path in processed:  # Handle symlinks
                    return
                processed.add(abs_path)
                
                # Get path properties
                is_dir = os.path.isdir(path)
                name = os.path.basename(path) or path
                
                # Calculate node properties
                if is_dir:
                    color = '#E8E8E8'  # Light gray for directories
                    size = self.min_size  # Fixed size for directories
                else:
                    ext = os.path.splitext(name)[1].lower()
                    color = self.file_colors.get(ext, '#FFFFFF')  # White default
                    size = self._calculate_node_size(self._get_file_size(path))
                
                # Add node with size-based dimensions
                dot.node(
                    rel_path,
                    name,
                    fillcolor=color,
                    width=str(size),
                    height=str(size)
                )
                
                # Add edge from parent
                if parent:
                    dot.edge(parent, rel_path)
                
                # Recurse into directories
                if is_dir:
                    try:
                        for entry in os.scandir(path):
                            add_path_to_graph(entry.path, rel_path, depth + 1)
                    except PermissionError:
                        self.logger.warning(f"Permission denied: {path}")
            
            # Start from root
            add_path_to_graph(root_path)
            
            # Save as SVG
            dot.render(self.map_path.replace('.svg', ''), format='svg', cleanup=True)
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

