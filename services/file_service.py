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

class FileService(BaseService):
    """Gère les opérations sur les fichiers"""

    def __init__(self, web_instance):
        super().__init__(web_instance)
        self.content_cache = {}
        self.last_modified = {}
        self.file_manager = FileManager(web_instance=web_instance, on_content_changed=None)
        
    @safe_operation()
    def read_file(self, file_path: str) -> Optional[str]:
        """Lit le contenu d'un fichier avec cache"""
        try:
            self._validate_file_path(file_path)
            
            # Vérifier le cache
            if file_path in self.content_cache:
                cache_time = self.last_modified.get(file_path, 0)
                if os.path.getmtime(file_path) <= cache_time:
                    return self.content_cache[file_path]
            
            # Lire le fichier
            with portalocker.Lock(file_path, 'r', timeout=10) as f:
                content = f.read()
                
            # Mettre en cache
            self.content_cache[file_path] = content
            self.last_modified[file_path] = os.path.getmtime(file_path)
            
            return content
            
        except Exception as e:
            self._handle_error('read_file', e)
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
    def ensure_mission_files(self, mission_name: str) -> bool:
        """S'assure que tous les fichiers requis existent pour une mission"""
        try:
            mission_dir = os.path.join("missions", mission_name)
            os.makedirs(mission_dir, exist_ok=True)
            
            required_files = [
                "demande.md",
                "specifications.md",
                "management.md", 
                "production.md",
                "evaluation.md",
                "suivi.md"
            ]
            
            for filename in required_files:
                file_path = os.path.join(mission_dir, filename)
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("")  # Créer fichier vide
                        
            return True
            
        except Exception as e:
            self._handle_error('ensure_mission_files', e)
            return False

    @safe_operation()
    def get_file_content(self, mission_id: int, file_path: str) -> Optional[str]:
        """Récupère le contenu d'un fichier de mission"""
        try:
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
