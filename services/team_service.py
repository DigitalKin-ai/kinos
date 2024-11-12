import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import traceback
from utils.logger import Logger
from utils.path_manager import PathManager
from utils.exceptions import ServiceError
from services.agent_service import AgentService
from services.mission_service import MissionService
from agents.kinos_agent import KinOSAgent

class TeamService:
    """Service simplifié pour la gestion des équipes en CLI"""
    
    def __init__(self, web_instance):
        """Initialize team service with simplified dependencies"""
        self.logger = Logger()
        self.agent_service = AgentService(None)
        
        # Initialize attributes
        self.teams = {}
        self.active_team = None
        self.predefined_teams = self._load_predefined_teams()

    def _load_predefined_teams(self) -> List[Dict]:
        """Load predefined team configurations"""
        return [
            {
                'id': 'default',
                'name': 'Default Team',
                'agents': ['specifications', 'management', 'evaluation', 'chroniqueur', 'documentaliste']
            },
            {
                'id': 'coding',
                'name': 'Coding Team', 
                'agents': ['specifications', 'production', 'testing', 'validation', 'documentaliste']
            },
            {
                'id': 'literature-review',
                'name': 'Literature Review Team',
                'agents': ['specifications', 'management', 'evaluation', 'chroniqueur', 'documentaliste']
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
        """Launch a team in the specified directory"""
        try:
            # Récupérer l'équipe correspondante
            team = next((t for t in self._load_predefined_teams() if t['id'] == team_id), None)
            if not team:
                raise ValueError(f"Équipe {team_id} non trouvée")

            # Activation des agents de l'équipe
            activation_results = []
            for agent_name in team['agents']:
                try:
                    # Logique d'activation de l'agent
                    success = self.web_instance.agent_service.toggle_agent(agent_name, 'start')
                    activation_results.append({
                        'agent': agent_name,
                        'status': 'started' if success else 'failed'
                    })
                except Exception as agent_error:
                    activation_results.append({
                        'agent': agent_name,
                        'status': 'error',
                        'error': str(agent_error)
                    })

            return {
                'team': team,
                'activation_results': activation_results,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.log(f"Erreur lors de l'activation de l'équipe : {str(e)}", 'error')
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

    def activate_team(self, team_id: str) -> Dict[str, Any]:
        """Activate a team in current directory with enhanced error handling and agent initialization"""
        try:
            # Centralized logging and error handling
            def log_and_validate(message: str, level: str = 'info'):
                self.web_instance.log_message(message, level)

            log_and_validate(
                f"\n=== TEAM ACTIVATION START ===\n"
                f"Team ID: {team_id}\n"
                f"Timestamp: {datetime.now().isoformat()}"
            )

            # Use current directory as mission directory
            mission_dir = os.getcwd()
            self.logger.log(f"📂 Mission directory: {mission_dir}", 'debug')

            # Validate and get team configuration
            team = next((t for t in self.predefined_teams if t['id'] == team_id), None)
            if not team:
                raise ValueError(f"Team {team_id} not found")
                
            normalized_agents = self._normalize_agent_names(team['agents'])
            team['agents'] = normalized_agents

            log_and_validate(
                f"\n=== TEAM CONFIGURATION ===\n"
                f"Team Name: {team['name']}\n"
                f"Normalized Agents: {normalized_agents}", 
                'debug'
            )

            # Stop current active team and all agents
            if self.active_team:
                log_and_validate(f"🔄 Stopping current active team: {self.active_team['id']}")
                self.deactivate_team(self.active_team['id'])

            if hasattr(self.web_instance.agent_service, 'stop_all_agents'):
                log_and_validate("🛑 Stopping all agents before initialization")
                self.web_instance.agent_service.stop_all_agents()

            # Prepare configuration
            config = {
                "openai_api_key": self.web_instance.config.get("openai_api_key", ""),
                "mission_dir": mission_dir
            }

            # Initialize agents with error handling
            try:
                if hasattr(self.web_instance.agent_service, 'init_agents'):
                    log_and_validate("🚀 Initializing agents...")
                    self.web_instance.agent_service.init_agents(
                        config=config,
                        team_agents=team['agents']
                    )
                    log_and_validate("✅ Agents initialized successfully", 'success')
                else:
                    raise AttributeError("AgentService missing init_agents method")
            except Exception as init_error:
                log_and_validate(
                    f"\n=== AGENT INITIALIZATION FAILED ===\n"
                    f"Error: {str(init_error)}\n"
                    f"Traceback: {traceback.format_exc()}", 
                    'critical'
                )
                raise

            # Start team agents with comprehensive validation and logging
            activation_results = []
            log_and_validate("\n=== STARTING INDIVIDUAL AGENTS ===")
        
            for agent_name in team['agents']:
                try:
                    log_and_validate(f"▶️ Starting agent: {agent_name}")
                    self._validate_agent_name(agent_name)
                
                    if hasattr(self.web_instance.agent_service, 'toggle_agent'):
                        success = self.web_instance.agent_service.toggle_agent(
                            agent_name=agent_name,
                            action='start',
                            mission_dir=mission_dir
                        )
                        result = {
                            'agent': agent_name,
                            'success': success,
                            'error': None if success else f"Failed to start {agent_name}"
                        }
                        activation_results.append(result)
                    
                        status = "✅ Success" if success else "❌ Failed"
                        log_and_validate(f"{status} - Agent: {agent_name}", 
                                         'success' if success else 'error')
                    
                except Exception as e:
                    log_and_validate(
                        f"❌ Agent activation failed:\n"
                        f"Agent: {agent_name}\n"
                        f"Error: {str(e)}", 
                        'error'
                    )
                    activation_results.append({
                        'agent': agent_name,
                        'success': False,
                        'error': str(e)
                    })

            # Log final activation summary with helper function
            success_count = sum(1 for r in activation_results if r['success'])
            log_and_validate(
                f"\n=== TEAM ACTIVATION SUMMARY ===\n"
                f"Total Agents: {len(team['agents'])}\n"
                f"Successfully Started: {success_count}\n"
                f"Failed: {len(team['agents']) - success_count}", 
                'info'
            )

            self.active_team = team
        
            return {
                'team': team,
                'activation_results': activation_results,
                'metrics': self._calculate_team_metrics(team, self._get_agent_statuses(team))
            }

        except Exception as e:
            self.web_instance.log_message(
                f"\n=== TEAM ACTIVATION FAILED ===\n"
                f"Team: {team_id}\n"
                f"Error: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}", 
                'critical'
            )
            raise ServiceError(f"Failed to activate team: {str(e)}")

    def _get_agent_statuses(self, team: Dict[str, Any]) -> Dict[str, Any]:
        """Get status for all agents in a team"""
        agent_statuses = {}
        for agent_name in team['agents']:
            try:
                agent_status = self.web_instance.agent_service.get_agent_status(agent_name)
                agent_statuses[agent_name] = agent_status
            except Exception as e:
                self.web_instance.log_message(f"Error getting status for {agent_name}: {str(e)}", 'error')
                agent_statuses[agent_name] = {
                    'running': False,
                    'status': 'error',
                    'error': str(e)
                }
        return agent_statuses

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
            self.web_instance.log_message(f"🔄 Agent {agent_name} starting run loop", 'info')
            agent.run()  # Appel effectif de la méthode run()
        except Exception as e:
            self.web_instance.log_message(
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
