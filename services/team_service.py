import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import traceback
from utils.logger import Logger
from utils.path_manager import PathManager
from utils.exceptions import ServiceError
from services.agent_service import AgentService
from agents.kinos_agent import KinOSAgent

class TeamService:
    """Service simplifié pour la gestion des équipes en CLI"""
    
    def __init__(self, _):  # Keep parameter for compatibility but don't use it
        """Initialize with minimal dependencies"""
        self.logger = Logger()
        self.agent_service = AgentService(None)
        self.predefined_teams = self._load_predefined_teams()

    def _load_predefined_teams(self) -> List[Dict]:
        """Load simplified team configurations"""
        return [
            {
                'id': 'default',
                'name': 'Default Team', 
                'agents': ['specifications', 'management', 'evaluation']
            },
            {
                'id': 'coding',
                'name': 'Coding Team',
                'agents': ['specifications', 'production', 'testing']
            }
        ]

    def _normalize_agent_names(self, team_agents: List[str]) -> List[str]:
        """Normalize agent names"""
        normalized = []
        for agent in team_agents:
            norm_name = agent.lower().replace('agent', '').strip()
            normalized.append(norm_name)
        return normalized

    def start_team(self, team_id: str, base_path: Optional[str] = None) -> Dict[str, Any]:
        """Start team in current/specified directory"""
        try:
            mission_dir = base_path or os.getcwd()
            team = next((t for t in self.predefined_teams if t['id'] == team_id), None)
            if not team:
                raise ValueError(f"Team {team_id} not found")

            config = {'mission_dir': mission_dir}
            self.agent_service.init_agents(config, team['agents'])

            for agent_name in team['agents']:
                try:
                    self.agent_service.toggle_agent(agent_name, 'start', mission_dir)
                except Exception as e:
                    self.logger.log(f"Error starting agent {agent_name}: {str(e)}", 'error')

            return {
                'team_id': team_id,
                'mission_dir': mission_dir,
                'agents': team['agents']
            }

        except Exception as e:
            self.logger.log(f"Error starting team: {str(e)}", 'error')
            raise

    def get_available_teams(self) -> List[Dict[str, Any]]:
        """Get list of available teams"""
        try:
            teams = [
                {
                    'id': team['id'],
                    'name': team['name'],
                    'agents': team['agents'],
                    'status': 'available'
                }
                for team in self.predefined_teams
            ]
            
            self.logger.log(f"Retrieved {len(teams)} available teams", 'info')
            return teams
        except Exception as e:
            self.logger.log(f"Error getting available teams: {str(e)}", 'error')
            raise ServiceError(f"Failed to get teams: {str(e)}")

    def launch_team(self, team_id: str, base_path: Optional[str] = None) -> Dict[str, Any]:
        """Launch a team in the specified directory"""
        try:
            # Use current directory if not specified
            mission_dir = base_path or os.getcwd()
            
            self.logger.log(f"Starting team {team_id} in {mission_dir}")

            # Validate team exists
            team = next((t for t in self.predefined_teams if t['id'] == team_id), None)
            if not team:
                raise ValueError(f"Team {team_id} not found")

            # Initialize agents
            config = {'mission_dir': mission_dir}
            self.agent_service.init_agents(config, team['agents'])

            # Start each agent
            for agent_name in team['agents']:
                try:
                    self.agent_service.toggle_agent(agent_name, 'start', mission_dir)
                    self.logger.log(f"Started agent {agent_name}")
                except Exception as e:
                    self.logger.log(f"Error starting agent {agent_name}: {str(e)}", 'error')

            return {
                'team_id': team_id,
                'mission_dir': mission_dir,
                'agents': team['agents']
            }

        except Exception as e:
            self.logger.log(f"Error starting team: {str(e)}", 'error')
            raise


    def _calculate_team_metrics(self, team: Dict[str, Any], agent_status: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics for a team"""
        try:
            if not agent_status:
                return {}

            total_agents = len(team['agents'])
            metrics = {
                'efficiency': self._calculate_efficiency(agent_status),
                'health': self._calculate_health_score(agent_status),
                'agent_stats': {
                    'total': total_agents,
                    'active': sum(1 for status in agent_status.values() if status['running']),
                    'healthy': sum(1 for status in agent_status.values() if status['health']['is_healthy'])
                }
            }

            return metrics

        except Exception as e:
            self.logger.log(f"Error calculating team metrics: {str(e)}", 'error')
            return {}

    def _calculate_efficiency(self, agent_status: Dict[str, Any]) -> float:
        """Calculate team efficiency score"""
        if not agent_status:
            return 0.0
        
        weights = {
            'health': 0.4,
            'activity': 0.3,
            'response_time': 0.2,
            'resource_usage': 0.1
        }
        
        scores = {
            'health': self._calculate_health_score(agent_status),
        }
        
        return sum(score * weights[metric] for metric, score in scores.items())

    def cleanup(self) -> None:
        """Clean up team service resources"""
        try:
            self.agent_service.stop_all_agents()
            self.teams.clear()
            self.active_team = None
        except Exception as e:
            self.logger.log(f"Error in cleanup: {str(e)}", 'error')


    def _run_agent_wrapper(self, agent_name: str, agent: 'KinOSAgent') -> None:
        """
        Wrapper pour exécuter un agent dans un thread avec gestion des erreurs
        
        Args:
            agent_name: Nom de l'agent
            agent: Instance de l'agent
        """
        try:
            self.log_message(f"🔄 Agent {agent_name} starting run loop", 'info')
            agent.run()  # Appel effectif de la méthode run()
        except Exception as e:
            self.log_message(
                f"💥 Agent {agent_name} crashed:\n"
                f"Error: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}", 
                'error'
            )

    def _calculate_health_score(self, agent_status: Dict[str, Any]) -> float:
        """Calculate overall health score for the team"""
        try:
            if not agent_status:
                return 0.0

            total_score = 0
            for status in agent_status.values():
                if status['health']['is_healthy']:
                    total_score += 1
                else:
                    # Penalize based on consecutive no changes
                    penalty = min(status['health']['consecutive_no_changes'] * 0.1, 0.5)
                    total_score += (1 - penalty)

            return total_score / len(agent_status)

        except Exception as e:
            self.logger.log(f"Error calculating health score: {str(e)}", 'error')
            return 0.0
