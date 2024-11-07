"""
agents.py - Implémentation unifiée des agents Parallagon
"""
import os
from parallagon_agent import ParallagonAgent
from aider_agent import AiderAgent
from suivi_agent import SuiviAgent

__all__ = [
    'SpecificationsAgent',
    'ProductionAgent',
    'ManagementAgent',
    'EvaluationAgent',
    'ContexteAgent',
    'SuiviAgent'
]

def validate_prompt(prompt_file: str) -> bool:
    """Vérifie qu'un fichier prompt est valide"""
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier les éléments requis
        required_elements = [
            "{context}",  # Placeholder pour le contexte
            "Votre tâche",
            "Format de réponse"
        ]
        
        return all(element in content for element in required_elements)
        
    except Exception:
        return False

class SpecificationsAgent(AiderAgent):
    """Agent gérant les spécifications"""
    def __init__(self, config):
        super().__init__(config)
        self.prompt_file = "prompts/specifications.md"
        if not validate_prompt(self.prompt_file):
            raise ValueError(f"Invalid prompt file: {self.prompt_file}")

class ProductionAgent(AiderAgent):
    """Agent gérant la production"""
    def __init__(self, config):
        super().__init__(config)
        self.prompt_file = "prompts/production.md"

class ManagementAgent(AiderAgent):
    """Agent gérant le management"""
    def __init__(self, config):
        super().__init__(config)
        self.prompt_file = "prompts/management.md"
        
    def analyze(self):
        """Analyse spécifique pour le management"""
        super().analyze()
        # Ajouter logique spécifique au management

class EvaluationAgent(AiderAgent):
    """Agent gérant l'évaluation"""
    def __init__(self, config):
        super().__init__(config)
        self.prompt_file = "prompts/evaluation.md"
        
    def analyze(self):
        """Analyse spécifique pour l'évaluation"""
        super().analyze()
        # Ajouter logique spécifique à l'évaluation

class ContexteAgent(ParallagonAgent):
    """Agent gérant le contexte"""
    def __init__(self, config):
        super().__init__(config)
        self.prompt_file = "prompts/contexte.md"
        self.current_context = set()
        
    def analyze(self):
        """Analyse spécifique pour le contexte"""
        super().analyze()
        # Ajouter logique spécifique au contexte

    def _build_prompt(self, context: dict) -> str:
        """Charge et formate le prompt depuis le fichier"""
        try:
            with open(self.prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
                
            # Ajouter le timestamp au contexte
            from datetime import datetime
            context_with_timestamp = {
                **context,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
                
            return prompt_template.format(
                context=self._format_other_files(context),
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Ajouter le timestamp ici
            )
        except Exception as e:
            self.logger(f"Erreur chargement prompt: {e}")
            return super()._build_prompt(context)  # Fallback au prompt par défaut
