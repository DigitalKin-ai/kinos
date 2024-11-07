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
    
    def __init__(self, file_paths: Dict[str, str], on_content_changed=None):
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
        
    def create_mission_files(self, mission_name: str) -> bool:
        """Create a new mission directory with default files"""
        try:
            # Create mission directory
            mission_dir = os.path.join("missions", mission_name)
            os.makedirs(mission_dir, exist_ok=True)
            
            # Create default files with error handling
            files_created = True
            for file_name in ["demande", "specifications", "management", "production", "evaluation", "suivi"]:
                try:
                    file_path = os.path.join(mission_dir, f"{file_name}.md")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        initial_content = self._get_initial_content(file_name)
                        f.write(initial_content)
                except Exception as e:
                    print(f"Error creating {file_name}.md: {e}")
                    files_created = False
                    break
                    
            if not files_created:
                # Cleanup on failure
                import shutil
                shutil.rmtree(mission_dir, ignore_errors=True)
                return False
                
            return True
            
        except Exception as e:
            print(f"Error creating mission files: {e}")
            return False
        
    def _ensure_files_exist(self):
        """Create files if they don't exist in current mission folder"""
        # Skip if no mission is selected
        if not self.current_mission:
            return
            
        mission_dir = os.path.join("missions", self.current_mission)
        
        # Liste explicite des fichiers à créer
        required_files = [
            "demande.md",
            "specifications.md",
            "management.md",
            "production.md",
            "evaluation.md",
            "suivi.md",
        ]
        
        for file_name in required_files:
            try:
                file_path = os.path.join(mission_dir, file_name)
                if not os.path.exists(file_path):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        initial_content = self._get_initial_content(file_name.replace('.md', ''))
                        f.write(initial_content)
                    print(f"Created {file_name} with initial content")
                else:
                    print(f"Using existing file: {file_path}")
                    
            except Exception as e:
                raise self.FileError(f"Error with {file_name}: {str(e)}")

    def _get_initial_content(self, file_name: str) -> str:
        """Get initial content for a file based on its name"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if file_name == 'demande':
            return f"""# Demande Actuelle
[timestamp: {timestamp}]
[status: NEW]

Entrez votre demande ici...

# Historique des Demandes
- [INIT] Création du fichier"""
            
        elif file_name == 'specifications':
            return f"""# État Actuel
[status: INIT]
En attente de demande...

# Signaux

# Contenu Principal

# Historique
- [{timestamp}] Création du fichier"""
            
        elif file_name in ['management', 'production', 'evaluation']:
            return f"""# État Actuel
[status: INIT]
En attente d'initialisation...

# Signaux

# Contenu Principal

# Historique
- [{timestamp}] Création du fichier"""
            
        return ""  # Default empty content

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
                initial_content = self._get_initial_content(file_name.replace('.md', ''))
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(initial_content)
                return initial_content

            # Read existing file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.logger(f"Successfully read: {file_path}")
                return content
                
        except Exception as e:
            self.logger(f"Erreur lecture {file_name}: {str(e)}")
            return None
            
    def write_file(self, file_name: str, content: str) -> bool:
        """Write content to a file with locking"""
        try:
            # Get full path based on current mission
            if self.current_mission:
                file_path = os.path.join("missions", self.current_mission, f"{file_name}.md")
            else:
                file_path = self.file_paths.get(file_name)
                
            if not file_path:
                print(f"FileManager: Chemin non trouvé pour {file_name}")
                return False
                
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
        """Get initial content for all files"""
        try:
            # Read initial content from template files
            with open('templates/initial_content/demande.md', 'r', encoding='utf-8') as f:
                demande_content = f.read()
                
            # Return dictionary with template content
            return {
                "demande": demande_content,
                "specifications": """# Spécification de Sortie
En attente de nouvelles demandes...

# Critères de Succès
- Critère principal 1
  * Sous-critère A
  * Sous-critère B
- Critère principal 2
  * Sous-critère A
  * Sous-critère B""",

                "management": f"""# Consignes Actuelles
En attente de nouvelles directives...

# TodoList
- [ ] En attente de demandes

# Actions Réalisées
- [{datetime.now().strftime("%Y-%m-%d %H:%M")}] Création du fichier""",

                "production": """[En attente de contenu à produire...]""",

                "evaluation": """# Évaluations en Cours
- Critère 1: [⚠️] En attente
- Critère 2: [⚠️] En attente

# Vue d'Ensemble
- Progression: 0%
- Points forts: À déterminer
- Points à améliorer: À déterminer
- Statut global: EN_ATTENTE""",

                "suivi": f"""[{datetime.now().strftime("%H:%M:%S")}] Système réinitialisé.
[{datetime.now().strftime("%H:%M:%S")}] En attente de nouvelles actions..."""
            }
        except Exception as e:
            print(f"Error loading initial content templates: {e}")
            return {}
