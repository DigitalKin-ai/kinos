"""
MapService - Service for generating and managing project documentation map
"""
import os
from datetime import datetime
from typing import Dict, List, Tuple
from services.base_service import BaseService

class MapService(BaseService):
    """Manages project documentation mapping and size monitoring"""

    def __init__(self, web_instance):
        super().__init__(web_instance)
        self.map_file = "map.md"
        self.size_limits = {
            'warning': 2000,  # Lines triggering warning
            'error': 3000     # Lines triggering error
        }

    def generate_map(self) -> bool:
        """Generate project map file"""
        try:
            tree_content, warnings = self._scan_directory(os.getcwd())
            
            map_content = self._format_map_content(tree_content, warnings)
            
            return self._write_map_file(map_content)
            
        except Exception as e:
            self.logger.log(f"Error generating map: {str(e)}", 'error')
            return False

    def _scan_directory(self, path: str, prefix: str = "") -> Tuple[List[str], List[str]]:
        """Scan directory recursively and return tree structure and warnings"""
        try:
            tree_lines = []
            warnings = []
            
            # Get and sort directory contents
            items = sorted(os.listdir(path))
            
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = prefix + ("└── " if is_last else "├── ")
                full_path = os.path.join(path, item)
                
                if os.path.isdir(full_path):
                    # Handle directory
                    tree_lines.append(f"{current_prefix}📁 {item}/")
                    
                    # Recursively scan subdirectory
                    sub_prefix = prefix + ("    " if is_last else "│   ")
                    sub_tree, sub_warnings = self._scan_directory(full_path, sub_prefix)
                    tree_lines.extend(sub_tree)
                    warnings.extend(sub_warnings)
                    
                elif item.endswith('.md'):
                    # Handle markdown file
                    line_count = self._count_lines(full_path)
                    status_icon = self._get_status_icon(line_count)
                    
                    tree_lines.append(
                        f"{current_prefix}📄 {item} ({line_count} lines) {status_icon}"
                    )
                    
                    # Add warning if needed
                    warning = self._check_file_size(item, line_count)
                    if warning:
                        warnings.append(warning)
                        
            return tree_lines, warnings
            
        except Exception as e:
            self.logger.log(f"Error scanning directory: {str(e)}", 'error')
            return [], []

    def _count_lines(self, file_path: str) -> int:
        """Count number of lines in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def _get_status_icon(self, line_count: int) -> str:
        """Get status icon based on line count"""
        if line_count > self.size_limits['error']:
            return "🔴"
        elif line_count > self.size_limits['warning']:
            return "⚠️"
        return "✓"

    def _check_file_size(self, filename: str, line_count: int) -> str:
        """Generate warning message if file exceeds size limits"""
        if line_count > self.size_limits['error']:
            return f"🔴 {filename} needs consolidation (>{self.size_limits['error']} lines)"
        elif line_count > self.size_limits['warning']:
            return f"⚠️ {filename} approaching limit (>{self.size_limits['warning']} lines)"
        return ""

    def _format_map_content(self, tree_content: List[str], warnings: List[str]) -> str:
        """Format complete map.md content"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = [
            "# Project Map",
            f"Generated: {timestamp}\n",
            "## Document Tree",
            "📁 Project"
        ]
        
        # Add tree structure
        content.extend(tree_content)
        
        # Add warnings if any
        if warnings:
            content.extend([
                "\n## Warnings",
                *warnings
            ])
            
        return "\n".join(content)

    def _write_map_file(self, content: str) -> bool:
        """Write content to map file"""
        try:
            with open(self.map_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.log(f"Error writing map file: {str(e)}", 'error')
            return False

    def update_map(self) -> bool:
        """Update map after file changes"""
        return self.generate_map()

    def get_map_content(self) -> str:
        """Get current map content"""
        try:
            if os.path.exists(self.map_file):
                with open(self.map_file, 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            self.logger.log(f"Error reading map file: {str(e)}", 'error')
            return ""