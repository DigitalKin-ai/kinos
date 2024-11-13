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
    
    def __init__(self, _):  # Keep parameter for compatibility but don't use it
        """Initialize with minimal dependencies"""
        self.project_root = os.getcwd()
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
            
    def write_file(self, file_name: str, content: str) -> bool:
        """Write file with map update"""
        try:
            file_path = os.path.join(os.getcwd(), file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write to temporary file first
            temp_path = f"{file_path}.tmp"
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
                
                # Atomic rename
                os.replace(temp_path, file_path)
                
                # Update map after any file change except map (readonly).md itself
                if file_name != 'map (readonly).md':
                    from services import init_services
                    services = init_services(None)
                    services['map_service'].update_map()
                    
                return True
                
            finally:
                # Clean up temp file if it exists
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                        
        except Exception as e:
            self.logger.log(f"Error writing {file_name}: {str(e)}", 'error')
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
            
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get content of a file with caching"""
        try:
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            self.logger.log(f"Error reading file {file_path}: {str(e)}", 'error')
            return None

    def write_file_content(self, file_path: str, content: str) -> bool:
        """Write content to a file atomically"""
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write to temp file first
            temp_path = f"{file_path}.tmp"
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
                
                # Atomic rename
                os.replace(temp_path, file_path)
                return True
                
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                        
        except Exception as e:
            self.logger.log(f"Error writing file {file_path}: {str(e)}", 'error')
            return False
