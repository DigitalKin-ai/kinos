import os
import json
import portalocker
from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback
from utils.exceptions import ServiceError, ValidationError, ResourceNotFoundError, FileOperationError
from services.base_service import BaseService
from utils.path_manager import PathManager
from utils.logger import Logger
from utils.decorators import safe_operation

class FileManager:
    """Service for managing file operations"""
    
    def __init__(self, web_instance, on_content_changed=None):
        """Initialize with minimal dependencies"""
        self.project_root = os.getcwd()
        self._on_content_changed = on_content_changed
        self.logger = Logger()
        self.content_cache = {}



    def read_file(self, file_name: str) -> Optional[str]:
        """Read file with simplified path handling"""
        try:
            file_path = os.path.join(os.getcwd(), file_name)
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.log(f"Error reading {file_name}: {str(e)}", 'error')
            return None
            
    @safe_operation(max_retries=3, delay=1.0)
    def write_file(self, file_name: str, content: str) -> bool:
        """
        Write content to a file with locking and cache invalidation.
        
        Args:
            file_name: Name of file to write
            content: Content to write
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Log before writing
            self.logger.log(f"Writing to {file_name}, content length: {len(content)}", 'info')
            
            # Get absolute path based on current mission using PathManager
            if self.current_mission:
                file_path = os.path.join(PathManager.get_mission_path(self.current_mission), f"{file_name}.md")
            else:
                base_path = self.file_paths.get(file_name)
                if not base_path:
                    self.logger.log(f"FileManager: Path not found for {file_name}", 'error')
                    return False
                file_path = PathManager.normalize_path(base_path)
                
            # Log full path
            self.logger.log(f"Full path: {file_path}", 'debug')
            
            # Only proceed if it's demande.md or file exists
            if file_name == 'demande' or os.path.exists(file_path):
                # Check if content is unchanged
                cache_key = f"file:{file_path}"
                if os.path.exists(file_path):
                    current_content = self.read_file(file_name)
                    if current_content == content:
                        self.logger.log(f"Content unchanged for {file_name}, skipping write", 'debug')
                        return True
                        
                # Create parent directory if needed
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                # Use FileService for thread-safe writes
                success = self.web_instance.file_service.write_file(file_path, content)
                if not success:
                    raise FileOperationError(f"Failed to write to {file_path}")
                    
                # Invalidate cache
                if cache_key in self.content_cache:
                    del self.content_cache[cache_key]
        
            # Trigger notification with content
            if self.on_content_changed:
                panel_name = file_name.split('.')[0].capitalize()
                # Always flash on write, include content for immediate update
                self.on_content_changed(
                    file_path=file_path,
                    content=content,
                    panel_name=panel_name,
                    flash=True
                )
            
            return True
            
        except portalocker.LockException:
            self.logger.log(f"FileManager: Fichier {file_name} verrouillé", 'error')
            return False
        except Exception as e:
            self.logger.log(f"Erreur écriture fichier {file_name}: {e}", 'error')
            return False
            
    def reset_files(self) -> bool:
        """Reset all files to their initial state"""
        try:
            # Contenu initial par défaut
            initial_contents = {
                'demande': '# Mission Request\n\nDescribe the mission request here.',
                'specifications': '# Specifications\n\nDefine specifications here.',
                'evaluation': '# Evaluation\n\nEvaluation criteria and results.'
            }
            
            for file_name, content in initial_contents.items():
                if not self.write_file(file_name, content):
                    return False
            return True
        except Exception as e:
            self.logger.log(f"Error resetting files: {e}", 'error')
            return False
            
