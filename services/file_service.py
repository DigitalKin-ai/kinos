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
        # Use PathManager for project root
        self.project_root = PathManager.get_project_root()
        # Use the file_manager from web_instance instead of creating a new one
        self.file_manager = web_instance.file_manager
        

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
        """Read content from a file with caching and locking"""
        try:
            # Normalize file name
            if not file_name.endswith('.md'):
                file_name = f"{file_name}.md"

            # Construct absolute file path using PathManager
            if self.current_mission:
                file_path = os.path.join(PathManager.get_mission_path(self.current_mission), file_name)
            else:
                file_path = os.path.join(self.project_root, file_name)

            # Ne pas créer le fichier s'il n'existe pas
            if not os.path.exists(file_path):
                return None

            # Use centralized cache service
            cache_key = f"file:{file_path}"
            cached_content = self.web_instance.cache_service.get(cache_key)
            if cached_content is not None:
                return cached_content

            # Read with safe operation
            content = self._safe_file_operation('read', file_path)
            if content is not None:
                self.content_cache[cache_key] = (os.path.getmtime(file_path), content)
            return content
                
        except Exception as e:
            self.logger.log(f"Error reading {file_name}: {str(e)}", 'error')
            return None

    @safe_operation()
    def write_file(self, file_path: str, content: str) -> bool:
        """Écrit le contenu dans un fichier avec verrouillage"""
        try:
            # Créer le dossier parent si nécessaire
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Écrire avec verrouillage
            with portalocker.Lock(file_path, 'w', timeout=10) as f:
                f.write(content)
                
            # Invalider le cache
            if file_path in self.content_cache:
                del self.content_cache[file_path]
                del self.last_modified[file_path]
                
            return True
            
        except Exception as e:
            self._handle_error('write_file', e)
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
    def get_file_content(self, mission_id: int, file_path: str) -> Optional[str]:
        """Récupère le contenu d'un fichier de mission"""
        try:
            # Use relative paths for API endpoints
            endpoint = f"/api/missions/{mission_id}/files/{file_path}"
            # Obtenir les infos de la mission
            mission = self.web_instance.mission_service.get_mission(mission_id)
            if not mission:
                raise ValidationError("Mission not found")
                
            # Construire le chemin complet
            full_path = os.path.join("missions", mission['name'], file_path)
            
            # Vérifier et lire le fichier
            if not os.path.exists(full_path):
                raise FileOperationError(f"File not found: {file_path}")
                
            return self.read_file(full_path)
            
        except Exception as e:
            self._handle_error('get_file_content', e)
            return None

    def cleanup(self):
        """Nettoie les ressources du service"""
        self.content_cache.clear()
        self.last_modified.clear()
