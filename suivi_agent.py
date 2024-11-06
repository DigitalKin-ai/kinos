"""
SuiviAgent - Agent responsable du suivi et de la synthèse des activités.

Responsabilités principales:
- Surveille tous les documents et logs
- Fournit des résumés concis des changements
- Maintient un historique chronologique des événements
"""
from parallagon_agent import ParallagonAgent
import time
from datetime import datetime

class SuiviAgent(ParallagonAgent):
    """Agent gérant le suivi et la synthèse des activités"""
    
    def __init__(self, config):
        super().__init__(config)
        self.logs_buffer = config.get("logs_buffer", [])
        self.last_summary_time = None

    def _clean_old_entries(self, content: str, max_entries: int = 100) -> str:
        """Keep only the most recent entries"""
        lines = content.split('\n')
        entries = []
        current_entry = []
        
        for line in lines:
            if line.startswith('[') and ']' in line:
                if current_entry:
                    entries.append('\n'.join(current_entry))
                current_entry = [line]
            elif current_entry:
                current_entry.append(line)
                
        if current_entry:
            entries.append('\n'.join(current_entry))
            
        # Keep only the most recent entries
        recent_entries = entries[-max_entries:] if entries else []
        return '\n'.join(recent_entries)

    def determine_actions(self) -> None:
        try:
            self.logger(f"[{self.__class__.__name__}] Analyse des activités...")
            
            current_time = datetime.now()
            if (self.last_summary_time is None or 
                (current_time - self.last_summary_time).total_seconds() >= 30):
                
                context = {
                    "suivi": {"suivi.md": self.current_content},  # Wrap in dict
                    "other_files": self.other_files,  # This is already a dict
                    "logs": self.logs_buffer[-50:]
                }
                
                response = self._get_llm_response(context)
                if response and response != self.current_content:
                    timestamp = current_time.strftime("%H:%M:%S")
                    new_entry = f"[{timestamp}] {response}"
                    
                    # Combine and clean entries
                    new_content = f"{self.current_content}\n\n{new_entry}" if self.current_content else new_entry
                    cleaned_content = self._clean_old_entries(new_content)
                    
                    # Write to file
                    with open(self.file_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    self.current_content = cleaned_content
                    self.last_summary_time = current_time
                    self.logger(f"[{self.__class__.__name__}] ✓ Nouveau résumé ajouté")
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur: {str(e)}")

    def _build_prompt(self, context: dict) -> str:
        return f"""Vous êtes l'agent de suivi. Votre rôle est de fournir des résumés concis des activités.

Contexte actuel :
{self._format_other_files(context['other_files'])}

Derniers Suivis :
{self._format_other_files(context['suivi'])}

Logs récents :
{self._format_logs(context['logs'])}

Votre tâche :
Fournir UNE SEULE phrase résumant ce qui s'est passé depuis le dernier message.

IMPORTANT:
- Une seule phrase
- Style factuel et concis
- Se concentrer sur les changements significatifs
- Ne pas répéter les informations déjà mentionnées dans les derniers suivis
- Si rien de significatif ne s'est passé, ne rien retourner"""

    def _format_logs(self, logs: list) -> str:
        """Format logs for context"""
        formatted_logs = []
        for log in logs:
            timestamp = log.get('timestamp', '')
            level = log.get('level', 'info')
            message = log.get('message', '')
            formatted_logs.append(f"[{timestamp}] [{level}] {message}")
        return "\n".join(formatted_logs)
