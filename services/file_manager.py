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
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # Update map for any file except map.md itself
            if file_name != 'map.md' and hasattr(self.web_instance, 'map_service'):
                self.map_service.update_map()
                
            return True
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
            
