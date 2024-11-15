"""Team configuration and management service"""
import os
import json
from typing import Dict, Any, List, Optional, Tuple
from services.base_service import BaseService
from utils.exceptions import ServiceError
from utils.path_manager import PathManager

class TeamService(BaseService):
    """Manages team configurations and state"""

    def __init__(self, _):  # Keep parameter for compatibility but don't use it
        """Initialize with minimal dependencies"""
        super().__init__(_)
        self.active_team = None
        self.predefined_teams = self._load_predefined_teams()

    def _load_predefined_teams(self) -> List[Dict[str, Any]]:
        """Load predefined team configurations"""
        try:
            teams = []
            teams_dir = os.path.join(PathManager.get_kinos_root(), "teams")
            
            if not os.path.exists(teams_dir):
                self.logger.log("Teams directory not found", 'warning')
                return []
                
            # Load each team config
            for team_dir in os.listdir(teams_dir):
                config_path = os.path.join(teams_dir, team_dir, "config.json")
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            valid, error = self.validate_team_config(config)
                            if valid:
                                teams.append(config)
                            else:
                                self.logger.log(
                                    f"Invalid team config {team_dir}: {error}",
                                    'warning'
                                )
                    except Exception as e:
                        self.logger.log(
                            f"Error loading team {team_dir}: {str(e)}", 
                            'error'
                        )
            return teams

        except Exception as e:
            self.logger.log(f"Error loading predefined teams: {str(e)}", 'error')
            return []

    def get_team_config(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific team"""
        try:
            for team in self.predefined_teams:
                if team.get('id') == team_id:
                    return team
            return None
            
        except Exception as e:
            self.logger.log(f"Error getting team config: {str(e)}", 'error')
            return None

    def set_active_team(self, team_id: str) -> bool:
        """Set the active team configuration"""
        try:
            team_config = self.get_team_config(team_id)
            if not team_config:
                raise ServiceError(f"Team not found: {team_id}")
                
            self.active_team = team_config
            self.logger.log(f"Active team set to: {team_id}", 'success')
            return True
            
        except Exception as e:
            self.logger.log(f"Error setting active team: {str(e)}", 'error')
            return False

    def get_active_team(self) -> Optional[Dict[str, Any]]:
        """Get the currently active team configuration"""
        return self.active_team

    def get_team_agents(self, team_id: Optional[str] = None) -> List[str]:
        """Get list of agent names for a team"""
        try:
            # Use active team if no ID provided
            config = self.get_team_config(team_id) if team_id else self.active_team
            
            if not config:
                return []
                
            # Extract agent names
            agents = []
            for agent in config.get('agents', []):
                if isinstance(agent, dict):
                    agents.append(agent['name'])
                else:
                    agents.append(agent)
                    
            return agents
            
        except Exception as e:
            self.logger.log(f"Error getting team agents: {str(e)}", 'error')
            return []

    def validate_team_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate team configuration format"""
        try:
            # Check required fields
            required = ['id', 'name', 'agents']
            missing = [f for f in required if f not in config]
            if missing:
                return False, f"Missing required fields: {', '.join(missing)}"
                
            # Validate agents
            if not config['agents']:
                return False, "No agents defined"
                
            for agent in config['agents']:
                if isinstance(agent, dict):
                    if 'name' not in agent:
                        return False, f"Missing name in agent config: {agent}"
                elif not isinstance(agent, str):
                    return False, f"Invalid agent format: {agent}"
                    
            # Validate phase config if present
            if 'phase_config' in config:
                phase_config = config['phase_config']
                for phase in ['expansion', 'convergence']:
                    if phase in phase_config:
                        phase_data = phase_config[phase]
                        if not isinstance(phase_data.get('active_agents', []), list):
                            return False, f"Invalid {phase} phase configuration"
                            
            return True, None
            
        except Exception as e:
            return False, str(e)

    def get_team_metrics(self, team_id: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a team"""
        try:
            # Use active team if no ID provided
            config = self.get_team_config(team_id) if team_id else self.active_team
            
            if not config:
                return {}
                
            # Get agent service
            from services import init_services
            services = init_services(None)
            agent_service = services['agent_service']
            
            # Collect metrics
            metrics = {
                'total_agents': len(config['agents']),
                'active_agents': 0,
                'healthy_agents': 0,
                'error_count': 0
            }
            
            # Get status for each agent
            for agent_name in self.get_team_agents(team_id):
                status = agent_service.get_agent_status(agent_name)
                if status['running']:
                    metrics['active_agents'] += 1
                if status['health']['is_healthy']:
                    metrics['healthy_agents'] += 1
                metrics['error_count'] += getattr(status, 'error_count', 0)
                
            return metrics
            
        except Exception as e:
            self.logger.log(f"Error getting team metrics: {str(e)}", 'error')
            return {}

    def get_agent_prompt_path(self, team_id: str, agent_name: str) -> Optional[str]:
        """Get prompt file path for an agent in a team"""
        try:
            team_dir = os.path.join(PathManager.get_kinos_root(), "teams", team_id)
            prompt_file = os.path.join(team_dir, f"{agent_name.lower()}.md")
            
            if os.path.exists(prompt_file):
                return prompt_file
            return None
            
        except Exception as e:
            self.logger.log(f"Error getting agent prompt path: {str(e)}", 'error')
            return None

    def cleanup(self):
        """Cleanup team service resources"""
        try:
            self.active_team = None
            self.predefined_teams.clear()
        except Exception as e:
            self.logger.log(f"Error cleaning up team service: {str(e)}", 'error')
