import os
import json
import time
import sys
import random
import threading
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from datetime import datetime
from typing import Dict, Any, Optional, List
import traceback
from utils.logger import Logger
from utils.path_manager import PathManager
from utils.exceptions import ServiceError
from services.agent_service import AgentService
from agents.base.agent_base import AgentBase

# Known Aider initialization error patterns
AIDER_INIT_ERRORS = [
    "Can't initialize prompt toolkit",
    "No Windows console found", 
    "aider.chat/docs/troubleshooting/edit-errors.html"
]

class TeamService:
    """Service simplifié pour la gestion des équipes en CLI"""
    
    def __init__(self, _):  # Keep parameter for compatibility but don't use it
        """Initialize with minimal dependencies"""
        self.logger = Logger()
        self.agent_service = AgentService(None)
        self.predefined_teams = self._load_predefined_teams()
        self.max_concurrent_agents = 3  # Maximum concurrent agents
        self._agent_queue = Queue()  # Agent queue
        self._active_agents = set()  # Active agents tracking
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

    def _normalize_team_id(self, team_id: str) -> str:
        """Normalize team ID to handle different separator styles"""
        # Convert to lowercase and replace underscores and spaces with hyphens
        normalized = team_id.lower().replace('_', '-').replace(' ', '-')
        return normalized

    def start_team(self, team_id: str, base_path: Optional[str] = None) -> Dict[str, Any]:
        """Start team in current/specified directory"""
        started_agents = []  # Track started agents
        
        try:
            mission_dir = base_path or os.getcwd()
            
            # Normalize the requested team ID
            normalized_id = self._normalize_team_id(team_id)
            
            # Find team with normalized ID comparison
            team = next(
                (t for t in self.predefined_teams 
                 if self._normalize_team_id(t['id']) == normalized_id),
                None
            )
            
            if not team:
                available_teams = [t['id'] for t in self.predefined_teams]
                self.logger.log(
                    f"Team {team_id} not found. Available teams: {available_teams}",
                    'error'
                )
                raise ValueError(f"Team {team_id} not found")

            # Get services once and reuse
            from services import init_services
            services = init_services(None)
            phase_service = services['phase_service']
            map_service = services['map_service']

            # Generate map first to get token count
            map_service.generate_map()
            
            # Get phase status info directly from phase service
            phase_status = phase_service.get_status_info()
            
            # Log phase status with values from phase service
            self.logger.log(
                f"Current phase: {phase_status['phase']}\n"
                f"Total tokens: {phase_status['total_tokens']:,}\n"
                f"Usage: {phase_status['usage_percent']:.1f}%\n"
                f"Status: {phase_status['status_message']}\n"
                f"Headroom: {phase_status['headroom']:,} tokens", 
                'info'
            )

            # Filter agents based on current phase from phase status
            filtered_agents = self._filter_agents_by_phase(team['agents'], phase_status['phase'])
            
            if not filtered_agents:
                self.logger.log(
                    f"No agents available for phase {phase_status['phase']}. "
                    f"Original agents: {team['agents']}", 
                    'warning'
                )
                return {
                    'team_id': team['id'],
                    'mission_dir': mission_dir,
                    'agents': [],
                    'phase': phase_status['phase'],
                    'status': 'no_agents_for_phase'
                }

            # Initialize filtered agents
            config = {'mission_dir': mission_dir}
            self.agent_service.init_agents(config, filtered_agents)

            # Randomize agent order
            random_agents = filtered_agents.copy()
            random.shuffle(random_agents)

            # Create thread pool
            with ThreadPoolExecutor(max_workers=self.max_concurrent_agents) as executor:
                # Function to start an agent
                def start_agent(agent_name: str) -> bool:
                    try:
                        self.logger.log(f"Starting agent: {agent_name}", 'info')
                        success = self.agent_service.toggle_agent(agent_name, 'start', mission_dir)
                        if success:
                            with self._team_lock:
                                started_agents.append(agent_name)
                        return success
                    except Exception as e:
                        self.logger.log(f"Error starting agent {agent_name}: {str(e)}", 'error')
                        return False

                # Submit initial batch of agents
                futures = []
                initial_batch = random_agents[:self.max_concurrent_agents]
                remaining_agents = random_agents[self.max_concurrent_agents:]

                for agent_name in initial_batch:
                    futures.append(executor.submit(start_agent, agent_name))
                    time.sleep(5)  # Wait 5 seconds between each initial agent

                # Process results and add new agents as others complete
                while futures or remaining_agents:
                    # Wait for an agent to complete
                    done, futures = concurrent.futures.wait(
                        futures,
                        return_when=concurrent.futures.FIRST_COMPLETED
                    )

                    # For each completed agent
                    for future in done:
                        try:
                            success = future.result()
                            if success and remaining_agents:
                                # Start next agent
                                next_agent = remaining_agents.pop(0)
                                futures.add(executor.submit(start_agent, next_agent))
                                time.sleep(5)  # Wait 5 seconds before starting next agent
                        except Exception as e:
                            self.logger.log(f"Error processing agent result: {str(e)}", 'error')

            return {
                'team_id': team['id'],
                'mission_dir': mission_dir,
                'agents': started_agents,
                'phase': phase_status['phase'],
                'status': 'started' if started_agents else 'failed'
            }

        except Exception as e:
            self.logger.log(f"Error starting team: {str(e)}", 'error')
            # Stop any started agents in reverse order
            for agent_name in reversed(started_agents):
                try:
                    self.agent_service.toggle_agent(agent_name, 'stop', mission_dir)
                except Exception as cleanup_error:
                    self.logger.log(f"Error stopping agent {agent_name}: {str(cleanup_error)}", 'error')
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
    def _filter_agents_by_phase(self, agents: List[str], phase: str) -> List[str]:
        """Filter agents based on current phase"""
        # Get team configuration for the phase
        for team in self.predefined_teams:
            if any(agent in team['agents'] for agent in agents):
                # Found matching team, check phase config
                phase_config = team.get('phase_config', {}).get(phase.lower(), {})
                active_agents = phase_config.get('active_agents', [])
                
                if active_agents:
                    # Filter to keep only active agents that exist in the team
                    return [agent for agent in agents if agent in active_agents]
                
                # If no phase config or no active_agents defined, return all agents
                return agents
                
        # If no matching team found, return all agents
        return agents
