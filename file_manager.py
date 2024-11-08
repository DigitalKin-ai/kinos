"""
FileManager - Handles file operations for Parallagon GUI
"""
import os
import portalocker
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime

class FileManager:
    """Manages file operations for the GUI"""
    
    class FileError(Exception):
        """Exception personnalisée pour les erreurs de fichiers"""
        pass
    
    def __init__(self, file_paths: Dict[str, str], web_instance, on_content_changed=None):
        # Ensure all file paths are defined
        self.file_paths = {
            'demande': 'demande.md',
            'specifications': 'specifications.md',
            'management': 'management.md',
            'production': 'production.md',
            'evaluation': 'evaluation.md',
            'suivi': 'suivi.md'
        }
        # Override with provided paths
        if file_paths:
            self.file_paths.update(file_paths)
            
        self.on_content_changed = on_content_changed
        self.current_mission = None
        self.logger = print  # Par défaut, utiliser print
        self._ensure_files_exist()
        
        
    def _ensure_files_exist(self):
        """Create files if they don't exist in current mission folder"""
        # Skip if no mission is selected
        if not self.current_mission:
            return
            
        # Use mission service to ensure files exist
        if not self.web_instance.mission_service.ensure_mission_files(self.current_mission):
            raise self.FileError(f"Failed to ensure files exist for mission {self.current_mission}")


    def _log_message(self, message: str):
        """Méthode sécurisée pour le logging"""
        try:
            if hasattr(self, 'logger'):
                self.logger(message)
            else:
                print(message)
        except:
            print(message)  # Fallback ultime

    def read_file(self, file_name: str) -> Optional[str]:
        """Read content from a file"""
        try:
            # Normalize file name
            if not file_name.endswith('.md'):
                file_name = f"{file_name}.md"

            # Debug log
            # self.logger(f"Attempting to read: {file_name}")
            # self.logger(f"Current mission: {self.current_mission}")

            # Construct file path
            if self.current_mission:
                file_path = os.path.join("missions", self.current_mission, file_name)
            else:
                file_path = file_name  # Default to current directory

            # self.logger(f"Full path: {file_path}")

            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)

            # Create if doesn't exist
            if not os.path.exists(file_path):
                self.logger(f"Creating new file: {file_path}")
                initial_content = self.web_instance.mission_service._get_initial_content(file_name.replace('.md', ''))
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(initial_content)
                return initial_content

            # Read existing file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content
                
        except Exception as e:
            self.logger(f"Erreur lecture {file_name}: {str(e)}")
            return None
            
    def write_file(self, file_name: str, content: str) -> bool:
        """Write content to a file with locking"""
        try:
            # Log avant écriture
            self.logger(f"Writing to {file_name}, content length: {len(content)}")
            
            # Get full path based on current mission
            if self.current_mission:
                file_path = os.path.join("missions", self.current_mission, f"{file_name}.md")
            else:
                file_path = self.file_paths.get(file_name)
                
            # Log le chemin complet
            self.logger(f"Full path: {file_path}")
            
            if not file_path:
                print(f"FileManager: Chemin non trouvé pour {file_name}")
                return False
                
            # Si le fichier existe, vérifier son contenu actuel
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
                if current_content == content:
                    self.logger(f"Content unchanged for {file_name}, skipping write")
                    return True
                    
            # Create parent directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
            # Write with file locking
            with portalocker.Lock(file_path, timeout=10) as lock:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        
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
            print(f"FileManager: Fichier {file_name} verrouillé")
            return False
        except Exception as e:
            print(f"Erreur écriture fichier {file_name}: {e}")
            return False
            
    def reset_files(self) -> bool:
        """Reset all files to their initial state"""
        try:
            initial_contents = self._get_initial_contents()
            
            for file_name, content in initial_contents.items():
                if not self.write_file(file_name, content):
                    return False
            return True
        except Exception as e:
            print(f"Error resetting files: {e}")
            return False
            
    def _get_initial_contents(self) -> Dict[str, str]:
        """Get initial content for all files via MissionService"""
        try:
            if hasattr(self, 'web_instance') and self.web_instance:
                return self.web_instance.mission_service._get_initial_contents()
            else:
                self.logger("No web_instance available for getting initial contents")
                return {}
        except Exception as e:
            self.logger(f"Error getting initial contents: {e}")
            return {}
