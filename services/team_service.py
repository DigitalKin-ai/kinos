from typing import Dict, Any, Optional, List
from utils.exceptions import ServiceError, ValidationError, ResourceNotFoundError
from services.base_service import BaseService
from utils.path_manager import PathManager
from utils.logger import Logger

class TeamService(BaseService):
    """Service for managing teams and agent groupings"""
    
    def __init__(self, web_instance):
        super().__init__(web_instance)
        self.teams = {}
        self.active_team = None
        self._load_predefined_teams()
        self.logger = Logger()

    def _validate_team_id(self, team_id: str) -> None:
        """Validate team ID format and existence"""
        if not team_id or not isinstance(team_id, str):
            raise ValidationError("Invalid team ID format")
        if not any(t['id'] == team_id for t in self.predefined_teams):
            raise ResourceNotFoundError(f"Team {team_id} not found")

    def _validate_agent_name(self, agent_name: str) -> None:
        """Validate agent name format and existence"""
        if not agent_name or not isinstance(agent_name, str):
            raise ValidationError("Invalid agent name format")
        if agent_name.lower() not in self.web_instance.agent_service.agents:
            raise ResourceNotFoundError(f"Agent {agent_name} not found")

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
        """Activate a team for a mission with enhanced error handling"""
        try:
            self._validate_team_id(team_id)
            team = next(t for t in self.predefined_teams if t['id'] == team_id)

            # Stop current active team if exists
            if self.active_team:
                self.deactivate_team(self.active_team['id'])

            # Stop all agents first
            self.web_instance.agent_service.stop_all_agents()

            # Start team agents with validation
            activation_results = []
            for agent_name in team['agents']:
                try:
                    self._validate_agent_name(agent_name)
                    success = self.web_instance.agent_service.toggle_agent(agent_name, 'start')
                    activation_results.append({
                        'agent': agent_name,
                        'success': success
                    })
                except Exception as e:
                    self.logger.log(f"Error activating agent {agent_name}: {str(e)}", 'error')
                    activation_results.append({
                        'agent': agent_name,
                        'success': False,
                        'error': str(e)
                    })

            self.active_team = team
            self.logger.log(f"Team {team['name']} activated with results: {activation_results}", 'success')

            return {
                'team': team,
                'activation_results': activation_results,
                'metrics': self._calculate_team_metrics(team, self._get_agent_statuses(team))
            }

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
            if not agent_status:
                return {}

            total_agents = len(team['agents'])
            metrics = {
                'efficiency': self._calculate_efficiency(agent_status),
                'health': self._calculate_health_score(agent_status),
                'resource_usage': self._calculate_resource_usage(agent_status),
                'response_times': self._calculate_response_times(agent_status),
                'agent_stats': {
                    'total': total_agents,
                    'active': sum(1 for status in agent_status.values() if status['running']),
                    'healthy': sum(1 for status in agent_status.values() if status['health']['is_healthy'])
                }
            }

            # Add historical trends
            metrics['trends'] = self._get_team_history(team['id'])
            
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
            'activity': self._calculate_activity_score(agent_status),
            'response_time': self._calculate_response_time_score(agent_status),
            'resource_usage': self._calculate_resource_score(agent_status)
        }
        
        return sum(score * weights[metric] for metric, score in scores.items())

    def _calculate_resource_usage(self, agent_status: Dict[str, Any]) -> Dict[str, float]:
        """Calculate resource usage metrics"""
        return {
            'cpu_usage': self._get_average_cpu_usage(agent_status),
            'memory_usage': self._get_average_memory_usage(agent_status),
            'file_operations': self._get_file_operation_stats(agent_status)
        }

    def cleanup(self) -> None:
        """Cleanup team service resources"""
        try:
            if self.active_team:
                self.deactivate_team(self.active_team['id'])
            self.teams.clear()
            self.active_team = None
            self.logger.log("Team service cleanup completed", 'success')
        except Exception as e:
            self.logger.log(f"Error during team service cleanup: {str(e)}", 'error')

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
