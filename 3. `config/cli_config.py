from dataclasses import dataclass
from typing import Optional, List

@dataclass
class CLIConfig:
    """Configuration pour le CLI KinOS"""
    
    # Chemins par défaut
    DEFAULT_LOG_DIR: str = 'logs/cli'
    DEFAULT_LOG_FILE: str = 'team_launch_{timestamp}.log'
    
    # Paramètres par défaut
    DEFAULT_TIMEOUT: int = 3600  # 1 heure
    
    # Équipes prédéfinies
    PREDEFINED_TEAMS: List[dict] = [
        {
            'id': 'book-writing',
            'name': 'Book Writing Team',
            'description': 'Équipe pour la rédaction et documentation',
            'agents': [
                'SpecificationsAgent', 
                'ManagementAgent', 
                'EvaluationAgent', 
                'SuiviAgent', 
                'DocumentalisteAgent', 
                'DuplicationAgent', 
                'RedacteurAgent', 
                'ValidationAgent'
            ]
        },
        {
            'id': 'coding',
            'name': 'Coding Team',
            'description': 'Équipe pour le développement logiciel',
            'agents': [
                'SpecificationsAgent', 
                'ManagementAgent', 
                'ProductionAgent', 
                'TesteurAgent', 
                'EvaluationAgent', 
                'ValidationAgent'
            ]
        }
    ]
    
    @classmethod
    def get_team_details(cls, team_id: str) -> Optional[dict]:
        """
        Récupère les détails d'une équipe par son ID
        
        Args:
            team_id (str): Identifiant de l'équipe
        
        Returns:
            dict: Détails de l'équipe ou None
        """
        return next((team for team in cls.PREDEFINED_TEAMS if team['id'] == team_id), None)
