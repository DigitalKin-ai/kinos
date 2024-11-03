"""
FileManager - Handles file operations for Parallagon GUI
"""
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime

class FileManager:
    """Manages file operations for the GUI"""
    
    class FileError(Exception):
        """Exception personnalisée pour les erreurs de fichiers"""
        pass
    
    def __init__(self, file_paths: Dict[str, str]):
        self.file_paths = file_paths
        
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
        """Write content to a file"""
        try:
            file_path = self.file_paths.get(file_name)
            if not file_path:
                return False
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
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

            "production": """En attente de contenu à produire...""",

            "evaluation": """# Évaluations en Cours
- Critère 1: [⚠️] En attente
- Critère 2: [⚠️] En attente

# Vue d'Ensemble
- Progression: 0%
- Points forts: À déterminer
- Points à améliorer: À déterminer
- Statut global: EN_ATTENTE"""
        }
