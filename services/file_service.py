"""
FileService - Service de gestion des fichiers pour KinOS
"""
import os
import portalocker
from typing import Dict, Optional, List
from services.file_manager import FileManager
from datetime import datetime
from utils.exceptions import FileOperationError, ValidationError
from utils.decorators import safe_operation
from services.base_service import BaseService
from utils.path_manager import PathManager

class FileService(BaseService):
    """Gère les opérations sur les fichiers"""

    def __init__(self, web_instance):
        super().__init__(web_instance)
        self.content_cache = {}
        self.last_modified = {}
        self.project_root = os.getcwd()
        

    def _get_relative_path(self, file_path: str) -> str:
        """Get path relative to project root"""
        try:
            return os.path.relpath(file_path, self.project_root)
        except ValueError:
            return file_path

    def _safe_file_operation(self, operation: str, file_path: str, content: str = None) -> Optional[str]:
        """Centralized safe file operations with locking"""
        try:
            with portalocker.Lock(file_path, 'r' if operation == 'read' else 'w', timeout=10) as lock:
                if operation == 'read':
                    return lock.read()
                else:
                    lock.write(content)
                    return None
        except Exception as e:
            self.logger.log(f"Error in {operation} operation: {str(e)}", 'error')
            return None

    @safe_operation()
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
                
            # Update map after any file change except map (readonly).md itself
            if file_name != 'map (readonly).md':
                from services import init_services
                services = init_services(None)
                services['map_service'].update_map()
                
            return True
        except Exception as e:
            self.logger.log(f"Error writing {file_name}: {str(e)}", 'error')
            return False

    @safe_operation()
    def list_files(self, directory: str, pattern: str = None) -> List[str]:
        """Liste les fichiers d'un dossier avec filtre optionnel"""
        try:
            self._validate_input(directory=directory)
            
            files = []
            for root, _, filenames in os.walk(directory):
                for filename in filenames:
                    if not pattern or filename.endswith(pattern):
                        files.append(os.path.join(root, filename))
                        
            return files
            
        except Exception as e:
            self._handle_error('list_files', e)
            return []

    @safe_operation()
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Récupère le contenu d'un fichier"""
        try:
            # Vérifier et lire le fichier
            if not os.path.exists(file_path):
                raise FileOperationError(f"File not found: {file_path}")
                
            return self.read_file(file_path)
            
        except Exception as e:
            self._handle_error('get_file_content', e)
            return None

    def cleanup(self):
        """Nettoie les ressources du service"""
        self.content_cache.clear()
        self.last_modified.clear()
