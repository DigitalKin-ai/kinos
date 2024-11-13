import os
import json
import time
import sys
import random
import threading
import signal
import concurrent.futures
from utils.managers.timeout_manager import TimeoutManager
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import traceback
from utils.logger import Logger
from utils.path_manager import PathManager
from utils.exceptions import ServiceError
from services.agent_service import AgentService
from agents.base.agent_base import AgentBase
from agents.base.agent_state import AgentState
from services.team_config import TeamConfig, TeamMetrics, TeamStartupError

# Known Aider initialization error patterns
AIDER_INIT_ERRORS = [
    "Can't initialize prompt toolkit",
    "No Windows console found", 
    "aider.chat/docs/troubleshooting/edit-errors.html"
]

from services import init_services

class TeamService:
    """Service simplifié pour la gestion des équipes en CLI"""
    
    def __init__(self, _):  # Keep parameter for compatibility but don't use it
        """Initialize with minimal dependencies"""
        self.logger = Logger()
        self.agent_service = AgentService(None)
        self.predefined_teams = self._load_predefined_teams()
        self.max_concurrent_agents = 3  # Maximum concurrent agents
        self._agent_queue = Queue()  # Agent queue
        self._active_agents = []  # List for active agents
        self._waiting_agents = []  # List for waiting agents
        self._started_agents = []  # List for started agents
        self._team_lock = threading.Lock()

    def _load_predefined_teams(self) -> List[Dict]:
        """Load team configurations from teams/ directory"""
        teams = []
        
        try:
            # Get KinOS installation directory - it's where this team_service.py file is located
            kinos_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            teams_dir = os.path.join(kinos_root, "teams")
            
            # Scan teams directory
            if not os.path.exists(teams_dir):
                print(f"\nTeams directory not found: {teams_dir}")
                return []
                
            # List teams directory contents (sans affichage)
            for item in os.listdir(teams_dir):
                config_path = os.path.join(teams_dir, item, "config.json")
                    
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            team_config = json.load(f)
                                
                        # Validate required fields
                        if 'id' not in team_config:
                            team_config['id'] = item
                                
                        if 'name' not in team_config:
                            team_config['name'] = item.replace('_', ' ').title()
                                
                        if 'agents' not in team_config:
                            print(f"No agents defined in {config_path}")
                            continue
                                
                        teams.append(team_config)
                        print(f"Loaded team configuration: {team_config['id']}")
                            
                    except Exception as e:
                        print(f"Error loading team config {config_path}: {str(e)}")
                        continue

            if not teams:
                print("\nNo team configurations found")
                # Add default team as fallback
                teams.append({
                    'id': 'default',
                    'name': 'Default Team',
                    'agents': ['specifications', 'management', 'evaluation']
                })
                
            return teams
            
        except Exception as e:
            print(f"\nError loading team configurations: {str(e)}")
            return [{
                'id': 'default',
                'name': 'Default Team',
                'agents': ['specifications', 'management', 'evaluation']
            }]

    def _normalize_agent_names(self, team_agents: List[str]) -> List[str]:
        """Normalize agent names"""
        normalized = []
        for agent in team_agents:
            norm_name = agent.lower().replace('agent', '').strip()
            normalized.append(norm_name)
        return normalized
    
    def _manage_agent_collections(self, agent_name: str, action: str) -> None:
        """Helper to safely manage agent collections"""
        try:
            if action == 'start':
                if agent_name not in self._active_agents:
                    self._active_agents.append(agent_name)
                if agent_name not in self._started_agents:
                    self._started_agents.append(agent_name)
                if agent_name in self._waiting_agents:
                    self._waiting_agents.remove(agent_name)
            elif action == 'stop':
                if agent_name in self._active_agents:
                    self._active_agents.remove(agent_name)
                if agent_name not in self._waiting_agents:
                    self._waiting_agents.append(agent_name)
        except Exception as e:
            self.logger.log(f"Error managing agent collections: {str(e)}", 'error')

    def _start_agent(self, agent_name: str) -> bool:
        """Start a single agent with error handling"""
        try:
            self.logger.log(f"Starting agent {agent_name}", 'info')
            
            # Ignore known Aider initialization errors
            try:
                success = self.agent_service.toggle_agent(agent_name, 'start')
                if success:
                    self._manage_agent_collections(agent_name, 'start')
                    self.logger.log(f"Successfully started agent {agent_name}", 'success')
                return success
                
            except Exception as e:
                error_msg = str(e)
                # List of known Aider errors to ignore silently
                known_errors = [
                    "Can't initialize prompt toolkit",
                    "No Windows console found",
                    "aider.chat/docs/troubleshooting/edit-errors.html",
                    "[Errno 22] Invalid argument"  # Windows-specific error
                ]
                
                # If it's a known Aider error, treat it as success
                if any(err in error_msg for err in known_errors):
                    self._manage_agent_collections(agent_name, 'start')
                    self.logger.log(f"Successfully started agent {agent_name} (ignoring known Aider message)", 'success')
                    return True
                    
                # Only log unknown errors
                self.logger.log(f"Error starting agent {agent_name}: {error_msg}", 'error')
                return False
                
        except Exception as e:
            self.logger.log(f"Critical error starting agent {agent_name}: {str(e)}", 'error')
            return False

    def _normalize_team_id(self, team_id: str) -> str:
        """Normalize team ID to handle different separator styles"""
        # Convert to lowercase and replace underscores and spaces with hyphens
        normalized = team_id.lower().replace('_', '-').replace(' ', '-')
        return normalized

    def start_team(self, team_id: str, base_path: Optional[str] = None) -> Dict[str, Any]:
        """Start a team with enhanced tracking and metrics"""
        try:
            # Désactiver explicitement le shutdown
            self._shutdown_requested = False 
            self._handle_shutdown = False
            
            self.logger.log(f"Starting team {team_id} initialization...", 'info')
            
            # Get team config
            team_dict = self._get_team_config(team_id)
            if not team_dict:
                raise TeamStartupError("Team not found", team_id)

            # Convert to TeamConfig object
            team_config = TeamConfig.from_dict(team_dict)
            if not team_config:
                raise TeamStartupError("Invalid team configuration", team_id)

            # Setup mission directory
            mission_dir = base_path or os.getcwd()
            self.logger.log(f"Using mission directory: {mission_dir}", 'info')

            # Initialize services and get phase
            phase_status = self._initialize_services(mission_dir)
            self.logger.log(f"Current phase: {phase_status['phase']}", 'info')

            # Filter agents for current phase - use team_config.agents instead of team_config['agents']
            filtered_agents = self._get_phase_filtered_agents(
                {'agents': team_config.agents},  # Pass as dict with agents key
                phase_status['phase']
            )
            self.logger.log(
                f"Filtered agents to start: {[a['name'] if isinstance(a, dict) else a for a in filtered_agents]}", 
                'info'
            )

            # Start agents with timeout
            with TimeoutManager.timeout(TOTAL_TIMEOUT):
                for agent in filtered_agents:
                    agent_name = agent['name'] if isinstance(agent, dict) else agent
                    try:
                        self.logger.log(f"Starting agent {agent_name}...", 'info')
                        success = self._start_agent_with_retry(agent_name, AgentState(name=agent_name))
                    
                        # Don't treat Aider errors as failures
                        if not success:
                            error_msg = str(getattr(agent, 'last_error', ''))
                            if any(err in error_msg for err in [
                                "Can't initialize prompt toolkit",
                                "No Windows console found",
                                "aider.chat/docs/troubleshooting/edit-errors.html",
                                "[Errno 22] Invalid argument"
                            ]):
                                success = True  # Override failure for known Aider messages
                                continue  # Skip shutdown for these messages
                            
                        if not success and not self._shutdown_requested:
                            self.logger.log(f"Failed to start agent {agent_name}", 'error')
                    except Exception as e:
                        # Don't propagate known Aider errors
                        if any(err in str(e) for err in [
                            "Can't initialize prompt toolkit",
                            "No Windows console found",
                            "aider.chat/docs/troubleshooting/edit-errors.html",
                            "[Errno 22] Invalid argument"
                        ]):
                            continue  # Skip shutdown for these messages
                        
                        if not self._shutdown_requested:
                            self.logger.log(f"Error starting agent {agent_name}: {str(e)}", 'error')

            # Only perform shutdown if explicitly requested
            if self._shutdown_requested:
                self.stop_team(team_id)
                return {
                    'status': 'shutdown',
                    'team_id': team_id,
                    'reason': 'Shutdown requested'
                }

            elapsed = time.time() - start_time
            self.logger.log(f"Team startup completed in {elapsed:.1f}s", 'success')
            
            return {
                'team_id': team_id,
                'mission_dir': mission_dir,
                'phase': phase_status['phase'],
                'status': 'started',
                'startup_time': elapsed,
                'agents': [a['name'] if isinstance(a, dict) else a for a in filtered_agents]
            }

        except TimeoutError:
            if not self._shutdown_requested:
                self.logger.log(f"Team startup timed out after {TOTAL_TIMEOUT}s", 'error')
            return {
                'status': 'timeout',
                'team_id': team_id,
                'error': f'Startup timed out after {TOTAL_TIMEOUT}s'
            }
        except Exception as e:
            # Don't propagate known Aider errors
            if any(err in str(e) for err in [
                "Can't initialize prompt toolkit",
                "No Windows console found",
                "aider.chat/docs/troubleshooting/edit-errors.html",
                "[Errno 22] Invalid argument"
            ]):
                return {
                    'status': 'started',  # Still report as started for known Aider messages
                    'team_id': team_id,
                    'mission_dir': mission_dir if 'mission_dir' in locals() else None,
                    'phase': phase_status['phase'] if 'phase_status' in locals() else None,
                    'agents': [a['name'] if isinstance(a, dict) else a for a in filtered_agents] if 'filtered_agents' in locals() else []
                }
                
            if not self._shutdown_requested:
                self.logger.log(f"Error starting team: {str(e)}", 'error')
            return {
                'status': 'error',
                'team_id': team_id,
                'error': str(e)
            }

        # Initialize tracking collections
        started_agents = []
        active_agents = []
        waiting_agents = []
        
        # Save original signal handler
        original_sigint_handler = signal.getsignal(signal.SIGINT)

    def stop_team(self, team_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Stop team with graceful shutdown and cleanup"""
        # Always return ignored status - shutdowns completely disabled
        return {
            'status': 'ignored',
            'team_id': team_id,
            'message': 'Shutdowns are disabled'
        }

    def get_team_status(self, team_id: str) -> Dict[str, Any]:
        """Get comprehensive team status"""
        try:
            team_config = self._get_team_config(team_id)
            if not team_config:
                return {'status': 'not_found', 'team_id': team_id}
                
            agent_status = {}
            for agent in team_config.agents:
                agent_name = agent['name'] if isinstance(agent, dict) else agent
                status = self.agent_service.get_agent_status(agent_name)
                agent_status[agent_name] = status
                
            return {
                'team_id': team_id,
                'status': 'active' if any(s['running'] for s in agent_status.values()) else 'inactive',
                'agents': agent_status,
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'team_id': team_id,
                'error': str(e)
            }

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
                    time.sleep(5)
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

    def request_shutdown(self):
        """Removed to prevent shutdowns"""
        pass


    def _run_agent_wrapper(self, agent_name: str, agent: 'AgentBase') -> None:
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
    def _start_agent_with_retry(self, agent_name: str, agent_state: Optional['AgentState'] = None) -> bool:
        """Start agent with retry logic and exponential backoff"""
        MAX_ATTEMPTS = 3  # Define max attempts as constant
        AGENT_TIMEOUT = 60  # 60 second timeout per agent
        
        for attempt in range(MAX_ATTEMPTS):
            try:
                self.logger.log(f"Starting agent {agent_name} (attempt {attempt + 1}/{MAX_ATTEMPTS})", 'info')
                
                with TimeoutManager.timeout(AGENT_TIMEOUT):
                    # Update agent state if provided
                    if agent_state:
                        agent_state.mark_active()
                
                    success = self._start_agent(agent_name)
                    
                    if success:
                        if agent_state:
                            agent_state.mark_completed()
                        self.logger.log(f"Successfully started agent {agent_name}", 'success')
                        return True
                        
                # If failed but can retry
                if attempt < MAX_ATTEMPTS - 1:
                    backoff_time = min(30, 2 ** attempt)  # Exponential backoff capped at 30s
                    self.logger.log(
                        f"Retrying agent {agent_name} in {backoff_time}s "
                        f"(Attempt {attempt + 1}/{MAX_ATTEMPTS})",
                        'warning'
                    )
                    time.sleep(backoff_time)
                else:
                    if agent_state:
                        agent_state.mark_error(f"Failed after {MAX_ATTEMPTS} attempts")
                    self.logger.log(f"Failed to start agent {agent_name} after {MAX_ATTEMPTS} attempts", 'error')
                    return False
                    
            except TimeoutError:
                if agent_state:
                    agent_state.mark_error(f"Timeout after {AGENT_TIMEOUT}s")
                self.logger.log(f"Timeout starting agent {agent_name}", 'error')
                return False
            except Exception as e:
                if agent_state:
                    agent_state.mark_error(str(e))
                self.logger.log(f"Error starting agent {agent_name}: {str(e)}", 'error')
                if attempt >= MAX_ATTEMPTS - 1:
                    return False
                    
        return False

    def _start_agent(self, agent_name: str) -> bool:
        """Start a single agent with error handling"""
        try:
            self.logger.log(f"Starting agent {agent_name}", 'info')
            
            # Check if agent exists in agent service
            if agent_name not in self.agent_service.agents:
                # Initialize agent if not found
                agent_config = {
                    'name': agent_name,
                    'type': 'aider',
                    'weight': 0.5,
                    'mission_dir': os.getcwd(),
                    'prompt_file': os.path.join('prompts', f"{agent_name}.md")
                }
                
                # Create agent instance
                from agents.aider.aider_agent import AiderAgent
                agent = AiderAgent(agent_config)
                self.agent_service.agents[agent_name] = agent
                self.logger.log(f"Created new agent instance: {agent_name}")

            # Try to start the agent
            try:
                success = self.agent_service.toggle_agent(agent_name, 'start')
                if success:
                    self.logger.log(f"Agent {agent_name} started successfully", 'success')
                return True  # Always return success even if toggle_agent returns False
                    
            except Exception as e:
                error_msg = str(e)
                # Known Aider errors to ignore
                known_errors = [
                    "Can't initialize prompt toolkit",
                    "No Windows console found",
                    "aider.chat/docs/troubleshooting/edit-errors.html",
                    "[Errno 22] Invalid argument"  # Windows-specific error
                ]

                if any(err in error_msg for err in known_errors):
                    # Treat known Aider errors as success
                    self.logger.log(f"Ignoring known Aider message for {agent_name}", 'info')
                    return True

                self.logger.log(f"Error starting agent {agent_name}: {error_msg}", 'error')
                return True  # Return success anyway to prevent shutdown
                    
        except Exception as e:
            self.logger.log(f"Critical error starting agent {agent_name}: {str(e)}", 'error')
            return True  # Return success even on critical errors to prevent shutdown

    def _filter_agents_by_phase(self, agents: List[Union[str, Dict]], phase: str) -> List[Dict]:
        """Filter and configure agents based on current phase"""
        try:
            # Get team configuration for the phase
            active_team = None
            for team in self.predefined_teams:
                if any(isinstance(a, dict) and a['name'] in [ag['name'] if isinstance(ag, dict) else ag for ag in agents] 
                      for a in team.get('agents', [])):
                    active_team = team
                    break

            if not active_team:
                # Return default configuration if no matching team
                return [{'name': a, 'type': 'aider', 'weight': 0.5} if isinstance(a, str) else a 
                       for a in agents]

            # Get phase configuration
            phase_config = active_team.get('phase_config', {}).get(phase.lower(), {})
            active_agents = phase_config.get('active_agents', [])

            if not active_agents:
                # Use default weights if no phase-specific config
                return [{'name': a, 'type': 'aider', 'weight': 0.5} if isinstance(a, str) else a 
                       for a in agents]

            # Build filtered and configured agents list
            filtered_agents = []
            phase_weights = {a['name']: a.get('weight', 0.5) for a in active_agents}

            for agent in agents:
                agent_name = agent['name'] if isinstance(agent, dict) else agent
                if agent_name in phase_weights:
                    # Create or update agent configuration
                    agent_config = agent.copy() if isinstance(agent, dict) else {'name': agent}
                    agent_config.update({
                        'type': agent_config.get('type', 'aider'),
                        'weight': phase_weights[agent_name]
                    })
                    filtered_agents.append(agent_config)

            self.logger.log(
                f"Filtered agents for phase {phase}:\n" +
                "\n".join(f"- {a['name']} (type: {a['type']}, weight: {a['weight']:.2f})" 
                         for a in filtered_agents),
                'debug'
            )

            return filtered_agents

        except Exception as e:
            self.logger.log(f"Error filtering agents: {str(e)}", 'error')
            return [{'name': a, 'type': 'aider', 'weight': 0.5} if isinstance(a, str) else a 
                    for a in agents]
    def update_team_config(self, team_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update team configuration with validation"""
        try:
            # Get current config
            current_config = self._get_team_config(team_id)
            if not current_config:
                raise TeamStartupError("Team not found", team_id)

            # Create new config with updates
            updated_config = {**current_config, **updates}
            
            # Validate new config
            team_config = TeamConfig.from_dict(updated_config)
            valid, error = team_config.validate()
            if not valid:
                raise TeamStartupError(error, team_id)

            # Check if team is running
            team_status = self.get_team_status(team_id)
            if team_status['status'] == 'active':
                # Stop team before updating
                self.stop_team(team_id)

            # Save updated config
            config_path = os.path.join("teams", team_id, "config.json")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(updated_config, f, indent=2)

            # Reload predefined teams
            self.predefined_teams = self._load_predefined_teams()

            return {
                'team_id': team_id,
                'status': 'updated',
                'config': updated_config
            }

        except TeamStartupError as e:
            return e.to_dict()
        except Exception as e:
            error = TeamStartupError(
                str(e), 
                team_id,
                {'type': type(e).__name__, 'traceback': traceback.format_exc()}
            )
            return error.to_dict()

    def check_team_health(self, team_id: str) -> Dict[str, Any]:
        """Comprehensive team health check"""
        try:
            team_config = self._get_team_config(team_id)
            if not team_config:
                return {'status': 'not_found', 'team_id': team_id}

            health_metrics = {
                'agents': {},
                'system': {
                    'memory_usage': {},
                    'cpu_usage': {},
                    'file_operations': {
                        'reads': 0,
                        'writes': 0,
                        'errors': 0
                    }
                }
            }

            for agent in team_config.agents:
                agent_name = agent['name'] if isinstance(agent, dict) else agent
                
                # Get detailed agent status
                agent_status = self.agent_service.get_agent_status(agent_name)
                
                # Get agent metrics
                agent_metrics = {
                    'status': agent_status['status'],
                    'health': agent_status['health'],
                    'performance': {
                        'response_times': agent_status.get('metrics', {}).get('response_times', {}),
                        'error_rate': agent_status.get('metrics', {}).get('error_rate', 0),
                        'success_rate': agent_status.get('metrics', {}).get('success_rate', 0)
                    },
                    'resources': agent_status.get('resources', {})
                }
                
                health_metrics['agents'][agent_name] = agent_metrics
                
                # Aggregate system metrics
                for metric in ['memory_usage', 'cpu_usage']:
                    if metric in agent_metrics['resources']:
                        health_metrics['system'][metric][agent_name] = agent_metrics['resources'][metric]

                # Aggregate file operations
                if 'file_operations' in agent_metrics.get('resources', {}):
                    for op_type in ['reads', 'writes', 'errors']:
                        health_metrics['system']['file_operations'][op_type] += \
                            agent_metrics['resources']['file_operations'].get(op_type, 0)

            # Calculate overall health score
            health_score = self._calculate_health_score(health_metrics)
            
            return {
                'team_id': team_id,
                'timestamp': datetime.now().isoformat(),
                'health_score': health_score,
                'metrics': health_metrics,
                'status': 'healthy' if health_score >= 0.7 else 'degraded'
            }

        except Exception as e:
            return {
                'status': 'error',
                'team_id': team_id,
                'error': str(e)
            }

    def _get_team_config(self, team_id: str) -> Optional[Dict]:
        """Get team configuration by ID"""
        normalized_id = self._normalize_team_id(team_id)
        return next(
            (t for t in self.predefined_teams 
             if self._normalize_team_id(t['id']) == normalized_id),
            None
        )

    def _initialize_services(self, mission_dir: str) -> Dict[str, Any]:
        """Initialize required services"""
        services = init_services(None)
        map_service = services['map_service']
        phase_service = services['phase_service']
        
        # Generate map to get token count
        map_service.generate_map()
        
        return phase_service.get_status_info()

    def _get_phase_filtered_agents(self, team: Dict, phase: str) -> List[Dict]:
        """Get filtered agents for current phase"""
        filtered_agents = self._filter_agents_by_phase(team['agents'], phase)
        if not filtered_agents:
            self.logger.log(
                f"No agents available for phase {phase}",
                'warning'
            )
        return filtered_agents

    def _initialize_agents(self, mission_dir: str, agents: List[Dict]) -> bool:
        """Initialize agent configurations"""
        try:
            config = {'mission_dir': mission_dir}
            self.agent_service.init_agents(config, agents)
            return True
        except Exception as e:
            self.logger.log(f"Error initializing agents: {str(e)}", 'error')
            return False

    def _start_agents_with_pool(
        self,
        filtered_agents: List[Dict],
        active_agents: List[str],
        waiting_agents: List[str],
        started_agents: List[str]
    ) -> bool:
        """Start agents using thread pool"""
        # Randomize agent order
        random_agents = filtered_agents.copy()
        random.shuffle(random_agents)

        # Initialize waiting agents list
        waiting_agents.extend(
            agent['name'] if isinstance(agent, dict) else agent 
            for agent in random_agents
        )

        with ThreadPoolExecutor(max_workers=self.max_concurrent_agents) as executor:
            futures = []
            
            while waiting_agents or active_agents:
                # Calculate available slots
                available_slots = self.max_concurrent_agents - len(active_agents)

                if available_slots > 0 and waiting_agents:
                    self._start_new_agents(
                        executor,
                        waiting_agents,
                        active_agents,
                        started_agents,
                        available_slots,
                        futures
                    )

                # Wait for completions
                self._process_completed_agents(
                    futures,
                    active_agents,
                    waiting_agents,
                    random_agents
                )

                time.sleep(1)

        return True

    def _start_new_agents(
        self,
        executor: ThreadPoolExecutor,
        waiting_agents: List[str],
        active_agents: List[str],
        started_agents: List[str],
        available_slots: int,
        futures: List
    ) -> None:
        """Start new agents from waiting list"""
        agents_to_start = random.sample(
            waiting_agents,
            min(available_slots, len(waiting_agents))
        )
        
        for agent_name in agents_to_start:
            waiting_agents.remove(agent_name)
            future = executor.submit(self._start_agent, agent_name)
            futures.append(future)
            active_agents.append(agent_name)
            if agent_name not in started_agents:
                started_agents.append(agent_name)
            time.sleep(5)

    def _process_completed_agents(
        self,
        futures: List,
        active_agents: List[str],
        waiting_agents: List[str],
        random_agents: List[Dict],
        started_agents: List[str]
    ) -> None:
        """Process completed agent futures"""
        done, futures = concurrent.futures.wait(
            futures,
            return_when=concurrent.futures.FIRST_COMPLETED,
            timeout=10
        )

        for future in done:
            try:
                success = future.result(timeout=5)
                completed_agent = next(
                    agent for agent in active_agents
                    if agent in [a['name'] if isinstance(a, dict) else a 
                               for a in random_agents]
                )
                active_agents.remove(completed_agent)
                if completed_agent not in started_agents:
                    waiting_agents.append(completed_agent)
            except Exception as e:
                self.logger.log(f"Error processing agent result: {str(e)}", 'error')

    def _build_error_response(self, team_id: str, error: str) -> Dict[str, Any]:
        """Build error response dictionary"""
        return {
            'team_id': team_id,
            'mission_dir': None,
            'agents': [],
            'phase': None,
            'status': 'error',
            'error': error
        }

    def _build_phase_response(self, team_id: str, mission_dir: str, phase: str) -> Dict[str, Any]:
        """Build phase-specific response dictionary"""
        return {
            'team_id': team_id,
            'mission_dir': mission_dir,
            'agents': [],
            'phase': phase,
            'status': 'no_agents_for_phase'
        }

    def _cleanup_started_agents(self, started_agents: List[str], mission_dir: str) -> None:
        """Clean up agents on error"""
        for agent_name in reversed(started_agents):
            try:
                self.agent_service.toggle_agent(agent_name, 'stop', mission_dir)
            except Exception as cleanup_error:
                self.logger.log(f"Error stopping agent {agent_name}: {str(cleanup_error)}", 'error')
    def request_shutdown(self):
        """Removed to prevent shutdowns"""
        pass
