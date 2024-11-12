import threading
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback
import time
from utils.exceptions import ServiceError, ValidationError, ResourceNotFoundError
from services.base_service import BaseService
from utils.path_manager import PathManager
from utils.logger import Logger
from services.agent_service import AgentService
from services.mission_service import MissionService
from services.file_manager import FileManager
from agents.kinos_agent import KinOSAgent

class TeamService(BaseService):
    """Service for managing teams and agent groupings"""
    
    def __init__(self, web_instance):
        # Import only what's needed
        from utils.logger import Logger
        from types import SimpleNamespace

        # Créer un web_instance par défaut s'il est None
        if web_instance is None:
            logger = Logger()
            web_instance = SimpleNamespace(
                logger=logger,
                log_message=lambda message, level='info': logger.log(message, level),
                agent_service=AgentService(None),
                mission_service=MissionService(),
                file_manager=FileManager(None, on_content_changed=None),
                config={},
                log=lambda message, level='info': logger.log(message, level)
            )

        # Vérification et ajout des attributs manquants
        if not hasattr(web_instance, 'logger'):
            web_instance.logger = Logger()
        
        if not hasattr(web_instance, 'log_message'):
            web_instance.log_message = lambda message, level='info': web_instance.logger.log(message, level)
        
        if not hasattr(web_instance, 'agent_service'):
            web_instance.agent_service = AgentService(None)
        
        if not hasattr(web_instance, 'mission_service'):
            web_instance.mission_service = MissionService()
        
        if not hasattr(web_instance, 'file_manager'):
            web_instance.file_manager = FileManager(web_instance, on_content_changed=None)

        # Initialiser le BaseService avec le logger
        super().__init__(web_instance.logger)

        # Stocker l'instance web
        self.web_instance = web_instance
        
        # Initialiser les attributs
        self.teams = {}
        self.active_team = None
        self.predefined_teams = self._load_predefined_teams()
        
        # Utiliser le logger de web_instance
        self.logger = web_instance.logger

    def _normalize_agent_names(self, team_agents: List[str]) -> List[str]:
        """
        Normalise les noms d'agents pour correspondre aux conventions
        
        Args:
            team_agents: Liste des noms d'agents à normaliser
            
        Returns:
            Liste des noms d'agents normalisés
        """
        normalized = []
        for agent in team_agents:
            # Supprimer 'Agent' et normaliser
            norm_name = agent.lower().replace('agent', '').strip()
            normalized.append(norm_name)
        return normalized

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

    def _load_predefined_teams(self) -> List[Dict]:
        """Load team configurations from files"""
        try:
            # Add default team configuration
            default_team = {
                'id': 'default',
                'name': 'Default Team',
                'agents': [
                    'specifications', 
                    'management', 
                    'evaluation', 
                    'chroniqueur', 
                    'documentaliste'
                ]
            }
            
            teams = [default_team]
            teams_dir = os.path.join(PathManager.get_project_root(), 'teams')
            
            if not os.path.exists(teams_dir):
                self.logger.log("Teams directory not found", 'warning')
                return teams
                
            # Scan team directories
            for team_dir in os.listdir(teams_dir):
                config_path = os.path.join(teams_dir, team_dir, 'config.json')
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            team_config = json.load(f)
                            teams.append(team_config)
                    except Exception as e:
                        self.logger.log(f"Error loading team config {team_dir}: {str(e)}", 'error')
                        continue
                        
            return teams
            
        except Exception as e:
            self.logger.log(f"Error loading predefined teams: {str(e)}", 'error')
            return [default_team]

    def get_predefined_teams(self):
        """
        Retourne la liste des équipes prédéfinies
    
        Returns:
            list: Liste des équipes disponibles
        """
        return self._load_predefined_teams()

    def activate_team(self, mission_id, team_id):
        """
        Active une équipe pour une mission avec gestion des logs
    
        Args:
            mission_id (int): ID de la mission
            team_id (str): ID de l'équipe
    
        Returns:
            dict: Résultat de l'activation avec informations de l'équipe
        """
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

    def get_teams_for_mission(self, mission_id: int) -> List[Dict[str, Any]]:
        """Get available teams for a mission"""
        try:
            # Use relative paths for any API endpoints
            endpoint = f"/api/missions/{mission_id}/teams"
            # Predefined teams with mission-specific modifications
            teams = [
                {
                    'id': f"{mission_id}_{team['id']}",  # Unique ID
                    'name': team['name'],
                    'mission_id': mission_id,
                    'agents': team['agents'],
                    'status': 'available'  # Add a status field
                } 
                for team in self.predefined_teams
            ]
            
            self.logger.log(f"Retrieved {len(teams)} teams for mission {mission_id}", 'info')
            return teams
        except Exception as e:
            self.logger.log(f"Error getting teams for mission {mission_id}: {str(e)}", 'error')
            raise ServiceError(f"Failed to get teams: {str(e)}")

    def launch_team(self, mission_id: int, team_id: str) -> Dict[str, Any]:
        """
        Lance une équipe complète pour une mission
        
        Args:
            mission_id: ID de la mission
            team_id: ID de l'équipe
            
        Returns:
            Dict avec les résultats du lancement
        """
        try:
            # 1. Activer l'équipe (initialisation)
            activation_result = self.activate_team(mission_id, team_id)
            
            # 2. Démarrer effectivement les agents
            start_result = self.start_team(mission_id, team_id)
            
            return {
                'activation': activation_result,
                'start': start_result,
                'status': 'running',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.web_instance.log_message(
                f"Failed to launch team {team_id} for mission {mission_id}: {str(e)}", 
                'error'
            )
            raise ServiceError(f"Team launch failed: {str(e)}")

    def activate_team(self, mission_id: int, team_id: str) -> Dict[str, Any]:
        """Activate a team for a mission with enhanced error handling and agent initialization"""
        try:
            # Centralized logging and error handling
            def log_and_validate(message: str, level: str = 'info'):
                self.web_instance.log_message(message, level)

            log_and_validate(
                f"\n=== TEAM ACTIVATION START ===\n"
                f"Mission ID: {mission_id}\n"
                f"Team ID: {team_id}\n"
                f"Timestamp: {datetime.now().isoformat()}"
            )

            # Get mission details with error handling
            mission = self.web_instance.mission_service.get_mission(mission_id)
            if not mission:
                log_and_validate(f"❌ Mission {mission_id} not found", 'error')
                raise ValueError(f"Mission {mission_id} not found")

            # Get mission directory
            mission_dir = PathManager.get_mission_path(mission['name'])
            log_and_validate(f"📂 Mission directory: {mission_dir}", 'debug')

            # Validate and get team configuration
            self._validate_team_id(team_id)
            team = next(t for t in self.predefined_teams if t['id'] == team_id)
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
        """Cleanup team service resources"""
        try:
            if self.active_team:
                self.deactivate_team(self.active_team['id'])
            self.teams.clear()
            self.active_team = None
            self.logger.log("Team service cleanup completed", 'success')
        except Exception as e:
            self.logger.log(f"Error during team service cleanup: {str(e)}", 'error')

    def start_team(self, mission_id: int, team_id: str, base_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Lance effectivement les agents d'une équipe en appelant leur méthode run()
        
        Args:
            mission_id: ID de la mission
            team_id: ID de l'équipe
            base_path: Chemin de base optionnel pour la mission
            
        Returns:
            Dict avec les résultats du lancement
        """
        try:
            # Utiliser PathManager pour obtenir le chemin de la mission
            mission_dir = PathManager.get_mission_path(base_path=base_path)
            
            self.web_instance.log_message(
                f"\n=== TEAM START SEQUENCE ===\n"
                f"Mission Directory: {mission_dir}\n"
                f"Team ID: {team_id}\n"
                f"Timestamp: {datetime.now().isoformat()}", 
                'info'
            )

            # Vérifier que l'équipe est active
            if not self.active_team or self.active_team['id'] != team_id:
                raise ValueError(f"Team {team_id} must be activated first")

            # Récupérer les agents de l'équipe
            team_agents = self.active_team['agents']
            self.web_instance.log_message(f"Starting {len(team_agents)} agents...", 'info')

            # Créer un thread pour chaque agent
            agent_threads = {}
            start_results = []

            for agent_name in team_agents:
                try:
                    # Récupérer l'instance de l'agent
                    agent = self.web_instance.agent_service.agents.get(agent_name.lower())
                    if not agent:
                        raise ValueError(f"Agent {agent_name} not found")

                    # Définir le répertoire de mission pour l'agent
                    agent.mission_dir = mission_dir

                    self.web_instance.log_message(f"🚀 Starting agent thread: {agent_name}", 'info')
                    
                    # Créer et démarrer le thread
                    thread = threading.Thread(
                        target=self._run_agent_wrapper,
                        args=(agent_name, agent),
                        daemon=True,
                        name=f"Agent-{agent_name}"
                    )
                    thread.start()
                    
                    agent_threads[agent_name] = thread
                    start_results.append({
                        'agent': agent_name,
                        'status': 'started',
                        'thread_id': thread.ident
                    })
                    
                    self.web_instance.log_message(
                        f"✅ Agent {agent_name} thread started successfully", 
                        'success'
                    )

                    time.sleep(10) # Echelonner les lancements

                except Exception as e:
                    self.web_instance.log_message(
                        f"❌ Failed to start agent {agent_name}: {str(e)}", 
                        'error'
                    )
                    start_results.append({
                        'agent': agent_name,
                        'status': 'failed',
                        'error': str(e)
                    })

            # Stocker les threads dans le service
            self.agent_threads = agent_threads

            # Log résumé final
            success_count = sum(1 for r in start_results if r['status'] == 'started')
            self.web_instance.log_message(
                f"\n=== TEAM START SUMMARY ===\n"
                f"Total Agents: {len(team_agents)}\n"
                f"Successfully Started: {success_count}\n"
                f"Failed: {len(team_agents) - success_count}", 
                'info'
            )

            return {
                'team_id': team_id,
                'mission_dir': mission_dir,
                'start_results': start_results,
                'active_threads': len(agent_threads)
            }

        except Exception as e:
            self.web_instance.log_message(
                f"\n=== TEAM START FAILED ===\n"
                f"Error: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}", 
                'critical'
            )
            raise ServiceError(f"Failed to start team: {str(e)}")

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
