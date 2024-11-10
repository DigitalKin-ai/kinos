"""
agents.py - Implémentation unifiée des agents KinOS

Ce module contient les implémentations spécifiques des agents qui héritent
de AiderAgent. Chaque agent a un rôle et des responsabilités distincts dans
le processus de développement.
"""
from typing import Dict
from aider_agent import AiderAgent

class ValidationAgent(AiderAgent):
    """
    Agent responsable de la validation des livrables et de la conformité.
    
    Responsabilités:
    - Validation des spécifications
    - Vérification de la conformité
    - Mesures quantitatives
    - Validation des critères objectifs
    """
    def __init__(self, config: Dict):
        if 'web_instance' not in config:
            raise ValueError("web_instance manquant dans la configuration")
            
        # Sauvegarder le répertoire original avant l'init parent
        self.original_dir = os.getcwd()
        
        # Obtenir la mission actuelle depuis le FileManager
        current_mission = getattr(config['web_instance'].file_manager, 'current_mission', None)
        
        # Permettre l'initialisation sans mission sélectionnée
        if current_mission:
            # Construire le chemin absolu vers la mission
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            mission_path = os.path.abspath(os.path.join(project_root, "missions", current_mission))
            config["mission_dir"] = mission_path
            self.mission_path = mission_path
        else:
            # Utiliser un chemin par défaut pour l'initialisation
            config["mission_dir"] = os.path.join("missions", "default")
            self.mission_path = None
        
        super().__init__(config)
        self.prompt_file = "prompts/validation.md"
        self.role = "validation"
        self.web_instance = config['web_instance']
        
    def start(self) -> None:
        """
        Démarre l'agent de validation en s'assurant qu'il travaille dans le bon répertoire.
        """
        try:
            # Obtenir la mission actuelle
            current_mission = getattr(self.web_instance.file_manager, 'current_mission', None)
            if not current_mission:
                raise ValueError("Cannot start validation agent: No mission selected")
                
            # Mettre à jour le chemin de mission
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.mission_path = os.path.abspath(os.path.join(project_root, "missions", current_mission))
            
            # Vérifier que le dossier mission existe
            if not os.path.exists(self.mission_path):
                raise ValueError(f"Mission directory not found: {self.mission_path}")
                
            # Changer vers le répertoire de mission
            os.chdir(self.mission_path)
            
            # Appeler le start parent
            super().start()
            
        except Exception as e:
            # En cas d'erreur, revenir au répertoire original
            os.chdir(self.original_dir)
            raise e
            
    def stop(self) -> None:
        """
        Arrête l'agent et restaure le répertoire de travail original.
        """
        try:
            super().stop()
        finally:
            # Toujours revenir au répertoire original
            os.chdir(self.original_dir)
import os
from typing import Dict, Optional
from agents.kinos_agent import KinOSAgent
from aider_agent import AiderAgent

# Discover and import all agent classes dynamically
agent_classes = {}
agent_types_module = importlib.import_module('.agent_types', package=__package__)

for name, obj in inspect.getmembers(agent_types_module):
    if (inspect.isclass(obj) and 
        issubclass(obj, AiderAgent) and 
        obj != AiderAgent):
        agent_classes[name] = obj

# Export discovered classes
__all__ = list(agent_classes.keys())
globals().update(agent_classes)

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
        if 'web_instance' not in config:
            raise ValueError("web_instance manquant dans la configuration")
        super().__init__(config)
        self.prompt_file = "prompts/specifications.md"
        self.role = "specifications"  # Using "specifications" consistently
        self.web_instance = config['web_instance']

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
        if 'web_instance' not in config:
            raise ValueError("web_instance manquant dans la configuration")
        super().__init__(config)
        self.prompt_file = "prompts/production.md"
        self.role = "production"
        self.web_instance = config['web_instance']

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
        if 'web_instance' not in config:
            raise ValueError("web_instance manquant dans la configuration")
        super().__init__(config)
        self.prompt_file = "prompts/management.md"
        self.role = "management"
        self.web_instance = config['web_instance']

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
        if 'web_instance' not in config:
            raise ValueError("web_instance manquant dans la configuration")
        super().__init__(config)
        self.prompt_file = "prompts/evaluation.md"
        self.role = "evaluation"
        self.web_instance = config['web_instance']

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
        # Ensure web_instance is in config before parent init
        if 'web_instance' not in config:
            raise ValueError("web_instance manquant dans la configuration")
        super().__init__(config)
        self.prompt_file = "prompts/suivi.md"
        self.role = "suivi"
        # Store web_instance explicitly
        self.web_instance = config['web_instance']

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
        if 'web_instance' not in config:
            raise ValueError("web_instance manquant dans la configuration")
        super().__init__(config)
        self.prompt_file = "prompts/duplication.md"
        self.role = "duplication"
        self.web_instance = config['web_instance']


class TesteurAgent(AiderAgent):
    """
    Agent responsable des tests et de la validation du code.
    
    Responsabilités:
    - Création et maintenance des tests
    - Exécution des suites de tests
    - Analyse des résultats
    - Identification des régressions
    - Suggestions d'amélioration
    - Validation de la couverture
    - Documentation des tests
    """
    def __init__(self, config: Dict):
        if 'web_instance' not in config:
            raise ValueError("web_instance manquant dans la configuration")
        super().__init__(config)
        self.prompt_file = "prompts/testeur.md"
        self.role = "testeur"
        self.web_instance = config['web_instance']

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
        if 'web_instance' not in config:
            raise ValueError("web_instance manquant dans la configuration")
        super().__init__(config)
        self.prompt_file = "prompts/documentaliste.md"
        self.role = "documentaliste"
        self.web_instance = config['web_instance']

class RedacteurAgent(AiderAgent):
    """
    Agent responsable de la rédaction et mise à jour du contenu textuel.
    
    Responsabilités:
    - Analyse des demandes de contenu
    - Génération de contenu textuel
    - Mise à jour des documents
    - Maintien de la cohérence du style
    - Validation des références
    - Vérification orthographique
    - Adaptation du style selon le contexte
    """
    def __init__(self, config: Dict):
        if 'web_instance' not in config:
            raise ValueError("web_instance manquant dans la configuration")
        super().__init__(config)
        self.prompt_file = "prompts/redacteur.md"
        self.role = "redacteur"
        self.web_instance = config['web_instance']


