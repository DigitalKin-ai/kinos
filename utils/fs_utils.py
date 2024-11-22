import os
import fnmatch
from typing import List, Set
from utils.logger import Logger

class FSUtils:
    """
    Utility class for file system operations and tree structure generation.
    
    Provides methods for:
    - File/folder filtering
    - Tree structure generation
    - Path validation
    - Gitignore integration
    """
    
    def __init__(self):
        self.logger = Logger()
        self.current_folder_path = None
        
    def get_folder_files(self, folder_path: str) -> list:
        """Get list of files in folder, respecting ignore patterns."""
        ignore_patterns = self._get_ignore_patterns()
        files = []
        
        for entry in os.scandir(folder_path):
            if entry.is_file():
                rel_path = os.path.relpath(entry.path, '.')
                if not self._should_ignore(rel_path, ignore_patterns):
                    files.append(entry.name)
                    
        return sorted(files)

    def get_subfolders(self, folder_path: str) -> list:
        """Get list of subfolders, respecting ignore patterns."""
        ignore_patterns = self._get_ignore_patterns()
        folders = []
        
        for entry in os.scandir(folder_path):
            if entry.is_dir():
                rel_path = os.path.relpath(entry.path, '.')
                if not self._should_ignore(rel_path, ignore_patterns):
                    folders.append(entry.name)
                    
        return sorted(folders)

    def build_tree_structure(self, current_path: str, files: list, subfolders: list, 
                           max_depth: int = 3, current_depth: int = 0, 
                           is_current_branch: bool = True) -> list:
        """Build tree structure with proper indentation and active folder highlighting."""
        tree = []
        
        # Initialize current_folder_path if None
        if self.current_folder_path is None:
            self.current_folder_path = ""
            
        # Handle None max_depth by setting it to a large number
        if max_depth is None:
            max_depth = float('inf')  # Use infinity for unlimited depth
        
        # Determine if this is the active folder
        is_active = os.path.abspath(current_path) == self.current_folder_path
        
        # Show root folder without indentation
        if current_depth == 0:
            active_indicator = "👉 " if is_active else ""
            tree.append(f"{active_indicator}📂 ./")
            base_indent = "   "  # Base indentation for root level items
        else:
            folder_name = os.path.basename(current_path)
            base_indent = "   " * current_depth
            active_indicator = "👉 " if is_active else ""
            tree.append(f"{base_indent}{active_indicator}📂 {folder_name}")
        
        # Add files with proper indentation
        for i, f in enumerate(files):
            prefix = "├─ " if (i < len(files) - 1 or subfolders) else "└─ "
            tree.append(f"{base_indent}{prefix}{f}")
        
        # Add subfolders without extra indentation
        for i, d in enumerate(subfolders):
            prefix = "├─ " if i < len(subfolders) - 1 else "└─ "
            subfolder_path = os.path.join(current_path, d)
            
            # Determine if this subfolder is part of current path
            is_current_subfolder = (is_current_branch and 
                                  self.current_folder_path and 
                                  subfolder_path in self.current_folder_path)
            
            if is_current_subfolder or current_depth < max_depth:
                sub_files = self.get_folder_files(subfolder_path)
                sub_folders = self.get_subfolders(subfolder_path)
                
                # Add subfolder and its contents
                subtree = self.build_tree_structure(
                    subfolder_path,
                    sub_files,
                    sub_folders,
                    max_depth,
                    current_depth + 1,
                    is_current_subfolder
                )
                tree.extend(subtree)
            else:
                # Just show folder name for depth-limited branches
                tree.append(f"{base_indent}{prefix}{d}/...")
        
        return tree

    def _get_ignore_patterns(self) -> List[str]:
        """Get list of patterns to ignore from .gitignore and defaults."""
        patterns = [
            '.git/*',
            '.git*',
            '.aider*',
            'node_modules',
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.DS_Store',
            'Thumbs.db'
        ]
        
        # Add patterns from .gitignore if it exists
        if os.path.exists('.gitignore'):
            try:
                with open('.gitignore', 'r', encoding='utf-8') as f:
                    patterns.extend(line.strip() for line in f 
                                  if line.strip() and not line.startswith('#'))
            except Exception as e:
                self.logger.warning(f"⚠️ Could not read .gitignore: {str(e)}")
        
        # Add patterns from .aiderignore if it exists        
        if os.path.exists('.aiderignore'):
            try:
                with open('.aiderignore', 'r', encoding='utf-8') as f:
                    patterns.extend(line.strip() for line in f 
                                  if line.strip() and not line.startswith('#'))
            except Exception as e:
                self.logger.warning(f"⚠️ Could not read .aiderignore: {str(e)}")
                
        return patterns

    def _should_ignore(self, path: str, ignore_patterns: List[str]) -> bool:
        """Check if a path should be ignored based on ignore patterns."""
        # Normalize path for consistent comparison
        path = path.replace('\\', '/')
        
        # Always ignore .git and .aider folders and files
        path_parts = path.split('/')
        if any(part.startswith(('.git', '.aider')) for part in path_parts):
            return True
            
        # Check against other ignore patterns
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False

    def set_current_folder(self, folder_path: str):
        """Set the current folder path for tree building."""
        self.current_folder_path = os.path.abspath(folder_path)
