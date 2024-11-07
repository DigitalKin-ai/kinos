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

class SuiviAgent(AiderAgent):
    """Agent gérant le Suivi"""
    def __init__(self, config):
        super().__init__(config)
        self.prompt_file = "prompts/suivi.md"

