"""
agents.py - Implémentation unifiée des agents Parallagon

Ce module contient les implémentations spécifiques des agents qui héritent
de AiderAgent. Chaque agent a un rôle et des responsabilités distincts dans
le processus de développement.
"""
import os
from typing import Dict, Optional
from parallagon_agent import ParallagonAgent
from aider_agent import AiderAgent

__all__ = [
    'SpecificationsAgent',
    'ProductionAgent', 
    'ManagementAgent',
    'EvaluationAgent',
    'SuiviAgent'
]

class SpecificationsAgent(AiderAgent):
    """
    Agent responsable de l'analyse des demandes et de la définition des spécifications.
    
    Responsabilités:
    - Analyse des demandes initiales
    - Définition des exigences techniques
    - Validation de la cohérence
    - Mise à jour continue des spécifications
    """
    def __init__(self, config: Dict):
        super().__init__(config)
        self.prompt_file = "prompts/specifications.md"
        self.role = "specifications"

class ProductionAgent(AiderAgent):
    """
    Agent responsable de la génération et optimisation du code.
    
    Responsabilités:
    - Génération de code
    - Implémentation des fonctionnalités
    - Respect des standards
    - Optimisation du code
    """
    def __init__(self, config: Dict):
        super().__init__(config)
        self.prompt_file = "prompts/production.md"
        self.role = "production"

class ManagementAgent(AiderAgent):
    """
    Agent responsable de la coordination et gestion du projet.
    
    Responsabilités:
    - Coordination des activités
    - Gestion des priorités
    - Suivi de l'avancement
    - Résolution des conflits
    """
    def __init__(self, config: Dict):
        super().__init__(config)
        self.prompt_file = "prompts/management.md"
        self.role = "management"

class EvaluationAgent(AiderAgent):
    """
    Agent responsable des tests et de la validation.
    
    Responsabilités:
    - Tests et validation
    - Contrôle qualité
    - Mesure des performances
    - Identification des améliorations
    """
    def __init__(self, config: Dict):
        super().__init__(config)
        self.prompt_file = "prompts/evaluation.md"
        self.role = "evaluation"

class SuiviAgent(AiderAgent):
    """
    Agent responsable du suivi et de la documentation.
    
    Responsabilités:
    - Journalisation des activités
    - Traçabilité des modifications
    - Génération de rapports
    - Historique des décisions
    """
    def __init__(self, config: Dict):
        super().__init__(config)
        self.prompt_file = "prompts/suivi.md"
        self.role = "suivi"

