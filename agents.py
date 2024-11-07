"""
agents.py - Implémentation unifiée des agents Parallagon
"""
import os
from parallagon_agent import ParallagonAgent
from aider_agent import AiderAgent

class SpecificationsAgent(AiderAgent):
    """Agent gérant les spécifications"""
    def __init__(self, config):
        super().__init__(config)
        self.prompt_file = "prompts/specifications.md"

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

class EvaluationAgent(AiderAgent):
    """Agent gérant l'évaluation"""
    def __init__(self, config):
        super().__init__(config)
        self.prompt_file = "prompts/evaluation.md"

class ContexteAgent(ParallagonAgent):
    """Agent gérant le contexte"""
    def __init__(self, config):
        super().__init__(config)
        self.prompt_file = "prompts/contexte.md"
        self.current_context = set()

    def _build_prompt(self, context: dict) -> str:
        """Charge et formate le prompt depuis le fichier"""
        try:
            with open(self.prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            return prompt_template.format(
                context=self._format_other_files(context)
            )
        except Exception as e:
            self.logger(f"Erreur chargement prompt: {e}")
            return super()._build_prompt(context)  # Fallback au prompt par défaut
