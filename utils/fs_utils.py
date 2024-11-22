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
        """
        Build tree structure with depth limits for non-current branches.
        
        Args:
            current_path: Path being analyzed
            files: List of files in current folder
            subfolders: List of subfolders
            max_depth: Maximum depth to show for non-current branches
            current_depth: Current recursion depth
            is_current_branch: Whether this is the branch containing current folder
            
        Returns:
            list: Lines of tree structure
        """
        tree = []
        path_parts = current_path.split(os.sep)
        base_indent = "   " * current_depth
        
        # Show current folder
        if current_depth == 0:
            tree.append("📂 ./")
        else:
            folder_name = path_parts[-1]
            tree.append(f"{base_indent}📂 {folder_name}")
        
        # Check depth limits for non-current branches
        if not is_current_branch and current_depth >= max_depth:
            if files or subfolders:
                tree.append(f"{base_indent}   ...")
            return tree
        
        # Add files
        for i, f in enumerate(files):
            prefix = "├─ " if (i < len(files) - 1 or subfolders) else "└─ "
            tree.append(f"{base_indent}   {prefix}{f}")
        
        # Add subfolders
        for i, d in enumerate(subfolders):
            prefix = "├─ " if i < len(subfolders) - 1 else "└─ "
            subfolder_path = os.path.join(current_path, d)
            
            # Determine if this subfolder is part of the current folder's path
            is_current_subfolder = is_current_branch and current_path in self.current_folder_path
            
            # Get subfolder contents if needed
            if is_current_subfolder or current_depth < max_depth:
                sub_files = self.get_folder_files(subfolder_path)
                sub_folders = self.get_subfolders(subfolder_path)
                
                # Recursively build subtree
                subtree = self.build_tree_structure(
                    subfolder_path,
                    sub_files,
                    sub_folders,
                    max_depth,
                    current_depth + 1,
                    is_current_subfolder
                )
                
                # Add subtree with proper prefix
                tree.extend([f"{base_indent}   {prefix}{line}" for line in subtree])
            else:
                # Just show folder name for depth-limited branches
                tree.append(f"{base_indent}   {prefix}{d}/")
        
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
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False

    def set_current_folder(self, folder_path: str):
        """Set the current folder path for tree building."""
        self.current_folder_path = os.path.abspath(folder_path)
