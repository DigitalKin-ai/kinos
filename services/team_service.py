from typing import Dict, Any, Optional, List
from utils.exceptions import ServiceError
from services.base_service import BaseService
from utils.path_manager import PathManager

class TeamService(BaseService):
    """Service for managing teams and agent groupings"""
    
    def __init__(self, web_instance):
        super().__init__(web_instance)
        self.teams = {}
        self.active_team = None
        self._load_predefined_teams()

    def _load_predefined_teams(self):
        """Load predefined team configurations"""
        self.predefined_teams = [
            {
                'id': 'book-writing',
                'name': 'Book Writing Team',
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
                'id': 'literature-review',
                'name': 'Literature Review Team',
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
                'agents': [
                    'SpecificationsAgent',
                    'ManagementAgent',
                    'EvaluationAgent',
                    'SuiviAgent',
                    'DocumentalisteAgent',
                    'DuplicationAgent',
                    'ProductionAgent',
                    'TesteurAgent',
                    'ValidationAgent'
                ]
            }
        ]

    def get_teams_for_mission(self, mission_id: int) -> List[Dict[str, Any]]:
        """Get available teams for a mission"""
        try:
            return self.predefined_teams
        except Exception as e:
            self.logger.log(f"Error getting teams: {str(e)}", 'error')
            raise ServiceError(f"Failed to get teams: {str(e)}")

    def activate_team(self, mission_id: int, team_id: str) -> Dict[str, Any]:
        """Activate a team for a mission"""
        try:
            # Find team configuration
            team = next((t for t in self.predefined_teams if t['id'] == team_id), None)
            if not team:
                raise ServiceError(f"Team {team_id} not found")

            # Stop current active team if exists
            if self.active_team:
                self.deactivate_team(self.active_team['id'])

            # Stop all agents
            self.web_instance.agent_service.stop_all_agents()

            # Start only agents in team
            for agent_name in team['agents']:
                try:
                    self.web_instance.agent_service.toggle_agent(agent_name, 'start')
                except Exception as e:
                    self.logger.log(f"Error starting agent {agent_name}: {str(e)}", 'error')

            self.active_team = team
            self.logger.log(f"Team {team['name']} activated", 'success')
            return team

        except Exception as e:
            self.logger.log(f"Error activating team: {str(e)}", 'error')
            raise ServiceError(f"Failed to activate team: {str(e)}")

    def deactivate_team(self, team_id: str) -> bool:
        """Deactivate a team"""
        try:
            if not self.active_team or self.active_team['id'] != team_id:
                return False

            # Stop all agents
            self.web_instance.agent_service.stop_all_agents()
            
            self.active_team = None
            self.logger.log(f"Team {team_id} deactivated", 'success')
            return True

        except Exception as e:
            self.logger.log(f"Error deactivating team: {str(e)}", 'error')
            raise ServiceError(f"Failed to deactivate team: {str(e)}")

    def get_team_status(self, team_id: str) -> Dict[str, Any]:
        """Get status of a team including agent states"""
        try:
            team = next((t for t in self.predefined_teams if t['id'] == team_id), None)
            if not team:
                raise ServiceError(f"Team {team_id} not found")

            # Get agent statuses with more detailed health info
            agent_status = {}
            for agent_name in team['agents']:
                agent = self.web_instance.agent_service.agents.get(agent_name.lower())
                if agent:
                    agent_status[agent_name] = {
                        'running': agent.running if hasattr(agent, 'running') else False,
                        'health': {
                            'is_healthy': agent.is_healthy() if hasattr(agent, 'is_healthy') else True,
                            'consecutive_no_changes': getattr(agent, 'consecutive_no_changes', 0),
                            'current_interval': agent.calculate_dynamic_interval() if hasattr(agent, 'calculate_dynamic_interval') else None
                        }
                    }

            return {
                'active': self.active_team and self.active_team['id'] == team_id,
                'agents': agent_status,
                'metrics': self._calculate_team_metrics(team, agent_status)
            }

        except Exception as e:
            self.logger.log(f"Error getting team status: {str(e)}", 'error')
            raise ServiceError(f"Failed to get team status: {str(e)}")

    def _calculate_team_metrics(self, team: Dict[str, Any], agent_status: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics for a team"""
        try:
            total_agents = len(team['agents'])
            active_agents = sum(1 for status in agent_status.values() if status['running'])
            healthy_agents = sum(1 for status in agent_status.values() 
                               if status['health']['is_healthy'])

            return {
                'efficiency': healthy_agents / total_agents if total_agents > 0 else 0,
                'active_ratio': active_agents / total_agents if total_agents > 0 else 0,
                'health_score': self._calculate_health_score(agent_status),
                'average_interval': sum(
                    status['health'].get('current_interval', 0) 
                    for status in agent_status.values()
                ) / total_agents if total_agents > 0 else 0
            }

        except Exception as e:
            self.logger.log(f"Error calculating team metrics: {str(e)}", 'error')
            return {}

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
