"""
SuiviAgent - Agent responsable du suivi et de la synthèse des activités
"""
from aider_agent import AiderAgent
from datetime import datetime

class SuiviAgent(AiderAgent):
    """Agent gérant le suivi et la synthèse des activités"""
    
    def _build_prompt(self, context: dict) -> str:
        return """Tu es un agent de suivi qui maintient un fichier markdown de logs.
        - Garde tous les logs existants
        - Ajoute les nouveaux logs en haut
        - Format: `[HH:MM:SS] Message`
        - Un log par ligne
        - Pas de formatage complexe
        """
    
    def write_log(self, message: str) -> bool:
        """Ajoute un nouveau log en préservant l'historique"""
        try:
            # Lire le contenu actuel
            current_content = self.read_files()
            if not current_content:
                current_content = ""
                
            # Créer le nouveau log
            timestamp = datetime.now().strftime("%H:%M:%S")
            new_log = f"[{timestamp}] {message}\n"
            
            # Combiner avec le contenu existant
            updated_content = new_log + current_content
            
            # Écrire le fichier mis à jour
            return self.write_file(updated_content)
            
        except Exception as e:
            print(f"Erreur d'écriture du log: {str(e)}")
            return False
