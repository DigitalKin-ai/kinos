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
        self.file_paths = file_paths
        self.on_content_changed = on_content_changed
        self._ensure_files_exist()
        
    def _ensure_files_exist(self):
        """Create files if they don't exist"""
        for name, file_path in self.file_paths.items():
            try:
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        initial_content = self._get_initial_content(name)
                        f.write(initial_content)
            except Exception as e:
                raise self.FileError(f"Error creating {file_path}: {str(e)}")

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

    def read_file(self, file_name: str) -> Optional[str]:
        """Read content from a file"""
        try:
            file_path = self.file_paths.get(file_name)
            if not file_path:
                raise self.FileError(f"Chemin non trouvé pour {file_name}")
                
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise self.FileError(f"Erreur lecture {file_name}: {str(e)}")
            
    def write_file(self, file_name: str, content: str) -> bool:
        """Write content to a file with locking"""
        try:
            file_path = self.file_paths.get(file_name)
            if not file_path:
                return False
                
            with open(file_path, 'w', encoding='utf-8') as f:
                portalocker.lock(f, portalocker.LOCK_EX)
                f.write(content)
                portalocker.unlock(f)
                
            # Mapping plus complet et cohérent
            panel_mapping = {
                "specifications": "Specification",
                "management": "Management", 
                "production": "Production",
                "evaluation": "Evaluation",
                "demande": "Demande"
            }
        
            # Appel du callback avec le nom du panneau correct
            if self.on_content_changed:
                panel_name = panel_mapping.get(file_name)
                if panel_name:
                    self.on_content_changed(file_path, content, panel_name)
                else:
                    self.on_content_changed(file_path, content)
                
            return True
        except Exception as e:
            print(f"Error writing file {file_name}: {e}")
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
        return {
            "demande": f"""# Demande Actuelle
[timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M")}]
[status: NEW]

Écrivez votre demande ici...

# Historique des Demandes""",

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

            "production": """# Contenu Initial
[En attente de contenu à produire...]""",

            "evaluation": """# Évaluations en Cours
- Critère 1: [⚠️] En attente
- Critère 2: [⚠️] En attente

# Vue d'Ensemble
- Progression: 0%
- Points forts: À déterminer
- Points à améliorer: À déterminer
- Statut global: EN_ATTENTE"""
        }
