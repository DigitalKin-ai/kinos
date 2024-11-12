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


    def get_mission_path(self, mission_name: str = None) -> str:
        """Now just returns current directory"""
        return os.getcwd()
        
    def _normalize_mission_name(self, mission_name: str) -> str:
        """
        Normalize mission name for filesystem use.
        Uses PathManager for consistent path normalization.
        """
        # First do basic character replacement
        invalid_chars = ["'", '"', ' ', '/', '\\', ':', '*', '?', '<', '>', '|']
        normalized = mission_name
        for char in invalid_chars:
            normalized = normalized.replace(char, '_')
            
        # Remove multiple consecutive underscores
        while '__' in normalized:
            normalized = normalized.replace('__', '_')
            
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        
        # Use PathManager for final normalization
        return PathManager.normalize_path(normalized)

    @property
    def current_mission(self):
        return self._current_mission

    @current_mission.setter 
    def current_mission(self, mission_name: str):
        """Setter with validation for current_mission"""
        if not mission_name:
            raise ValueError("Mission name cannot be empty")
            
        # Normalize mission name for filesystem
        normalized_name = self._normalize_mission_name(mission_name)
        
        self.logger.log(f"Setting current mission to: {mission_name} (normalized: {normalized_name})", 'info')
        
        # Use PathManager for mission directory path
        mission_dir = PathManager.get_mission_path(normalized_name)
        
        # Verify directory exists and is accessible
        if not os.path.exists(mission_dir):
            self.logger.log(f"❌ Mission directory not found: {mission_dir}", 'error')
            # Log parent directory contents for debugging
            parent_dir = os.path.dirname(mission_dir)
            if os.path.exists(parent_dir):
                self.logger.log(f"📂 Contents of parent directory {parent_dir}:", 'info')
                for item in os.listdir(parent_dir):
                    self.logger.log(f"- {item}", 'info')
            raise ValueError(f"Mission directory not found: {mission_dir}")
            
        if not os.access(mission_dir, os.R_OK | os.W_OK):
            self.logger.log(f"❌ Insufficient permissions on: {mission_dir}", 'error')
            raise ValueError(f"Insufficient permissions on: {mission_dir}")
            
        self._current_mission = mission_name  # Store original name
        self.logger.log(f"✓ Mission changed to: {mission_name}", 'success')
        
        
    def _ensure_files_exist(self):
        """No longer needs to create any initial files"""
        pass



    @safe_operation(max_retries=3, delay=1.0)
    def read_file(self, file_name: str) -> Optional[str]:
        """
        Read content from a file with caching and locking.
        
        Args:
            file_name: Name of file to read
            
        Returns:
            str: File contents or None if error
        """
        try:
            # Normalize file name
            if not file_name.endswith('.md'):
                file_name = f"{file_name}.md"

            # Get file path using PathManager
            file_path = (PathManager.get_mission_path(self.current_mission) if self.current_mission 
                        else PathManager.get_project_root())
            file_path = os.path.join(file_path, file_name)

            self.logger.log(f"Reading file: {file_path}", 'debug')

            # Check cache first
            cache_key = f"file:{file_path}"
            if cache_key in self.content_cache:
                mtime = os.path.getmtime(file_path)
                cached_time, cached_content = self.content_cache[cache_key]
                if mtime == cached_time:
                    self.logger.log(f"Cache hit for {file_path}", 'debug')
                    return cached_content

            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)

            # Ne pas créer le fichier s'il n'existe pas
            if not os.path.exists(file_path):
                return None

            # Read existing file with locking
            with portalocker.Lock(file_path, 'r', timeout=10) as lock:
                content = lock.read()
                # Cache the content
                self.content_cache[cache_key] = (os.path.getmtime(file_path), content)
                return content
                
        except Exception as e:
            self.logger.log(f"Erreur lecture {file_name}: {str(e)}", 'error')
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
            
