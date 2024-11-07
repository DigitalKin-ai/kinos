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

