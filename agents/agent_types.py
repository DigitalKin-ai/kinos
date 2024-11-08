"""
agents.py - Implémentation unifiée des agents KinOS

Ce module contient les implémentations spécifiques des agents qui héritent
de AiderAgent. Chaque agent a un rôle et des responsabilités distincts dans
le processus de développement.
"""
from typing import Dict, Optional
from .kinos_agent import KinOSAgent
from aider_agent import AiderAgent

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

class DuplicationAgent(AiderAgent):
    """
    Agent responsable de la détection et réduction de la duplication.
    
    Responsabilités:
    - Analyse du code source pour la duplication
    - Identification des fonctions similaires
    - Détection des configurations redondantes
    - Proposition de refactoring
    """
    def __init__(self, config: Dict):
        super().__init__(config)
        self.prompt_file = "prompts/duplication.md"
        self.role = "duplication"
        
    def _build_prompt(self, context: dict) -> str:
        """
        Surcharge pour ajouter des informations spécifiques à la détection de duplication
        """
        base_prompt = super()._build_prompt(context)
        # Add any duplication-specific context here
        return base_prompt

class DocumentalisteAgent(AiderAgent):
    """
    Agent responsable de la cohérence entre code et documentation.
    
    Responsabilités:
    - Analyse de la documentation existante
    - Détection des incohérences avec le code
    - Mise à jour de la documentation
    - Maintien de la qualité documentaire
    """
    def __init__(self, config: Dict):
        super().__init__(config)
        self.prompt_file = "prompts/documentaliste.md"
        self.role = "documentaliste"
        
    def _build_prompt(self, context: dict) -> str:
        """
        Surcharge pour ajouter des informations spécifiques à l'analyse de documentation
        """
        base_prompt = super()._build_prompt(context)
        # Add documentation-specific context here
        return base_prompt
