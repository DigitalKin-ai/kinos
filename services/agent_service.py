import os
import time
import threading
import traceback
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from utils.exceptions import AgentError
import importlib
import inspect
from agents.kinos_agent import KinOSAgent
from aider_agent import AiderAgent
from utils.path_manager import PathManager
from utils.validators import validate_agent_name
from utils.logger import Logger
import sys

class AgentService:
    def _normalize_agent_names(self, team_agents: List[str]) -> List[str]:
        """Normalise les noms d'agents pour correspondre aux conventions"""
        normalized = []
        for agent in team_agents:
            # Supprimer 'Agent' et normaliser
            norm_name = agent.lower().replace('agent', '').strip()
            normalized.append(norm_name)
        return normalized


    def __init__(self, web_instance):
        self.logger = Logger()
        self.agents = {}
        self.agent_threads = {}
        self._cleanup_lock = threading.Lock()

        # Set UTF-8 encoding for stdout/stderr
        import sys
        import codecs
        import locale
        
        # Force UTF-8 encoding
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        
        # Set locale to handle Unicode
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')
            except locale.Error:
                pass

    def validate_web_instance(self, web_instance):
        """
        Valide et complète une instance web avec des valeurs par défaut
        
        Args:
            web_instance: Instance web à valider
        
        Returns:
            Instance web complétée
        """
        from utils.logger import Logger
        from services.mission_service import MissionService
        from services.file_manager import FileManager
        from types import SimpleNamespace

        # Si None, créer une instance par défaut
        if web_instance is None:
            web_instance = SimpleNamespace(
                logger=Logger(),
                config={},
                mission_service=MissionService(),
                file_manager=FileManager(None)
            )

        # Ajouter des méthodes par défaut si manquantes
        if not hasattr(web_instance, 'logger'):
            web_instance.logger = Logger()
        
        if not hasattr(web_instance, 'log_message'):
            web_instance.log_message = lambda msg, level='info': web_instance.logger.log(msg, level)
        
        if not hasattr(web_instance, 'mission_service'):
            web_instance.mission_service = MissionService()
        
        if not hasattr(web_instance, 'file_manager'):
            web_instance.file_manager = FileManager(web_instance)

        return web_instance

    def _discover_agents(self) -> List[Dict[str, str]]:
        """Discover available agents by scanning prompts directory"""
        discovered_agents = []
        # Get prompts directory using PathManager
        prompts_dir = PathManager.get_prompts_path()
        
        try:
            # Create prompts directory if it doesn't exist
            if not os.path.exists(prompts_dir):
                os.makedirs(prompts_dir)
                self.web_instance.log_message("Created prompts directory", 'info')
                return []

            # Get prompts directory using PathManager
            prompts_dir = PathManager.get_prompts_path()
            
            # Scan for .md files in prompts directory
            for file in os.listdir(prompts_dir):
                if file.endswith('.md'):
                    agent_name = file[:-3].lower()  # Remove .md extension
                    agent_class = self._get_agent_class(agent_name)
                    if agent_class:
                        discovered_agents.append({
                            'name': agent_name,
                            'prompt_file': file,
                            'class': agent_class,
                            'status': self._get_agent_status(agent_name)
                        })
                        self.web_instance.log_message(f"Discovered agent: {agent_name}", 'debug')

            return discovered_agents

        except Exception as e:
            self.web_instance.log_message(f"Error discovering agents: {str(e)}", 'error')
            return []

    def _get_agent_class(self, agent_name: str):
        """Get the appropriate agent class based on name"""
        try:
            # Import the AiderAgent class dynamically
            from aider_agent import AiderAgent
            
            # All agents use AiderAgent as base class
            return AiderAgent
            
        except ImportError as e:
            self.web_instance.log_message(f"Error importing agent class: {str(e)}", 'error')
            return None

    def init_agents(self, config: Dict[str, Any], team_agents: Optional[List[str]] = None) -> None:
        """Initialise les agents pour une équipe"""
        try:
            # Normaliser les noms d'agents
            if not team_agents:
                team_agents = [
                    'specifications', 'management', 'evaluation', 
                    'chroniqueur', 'documentaliste', 'production', 'testeur'
                ]

            normalized_agents = [
                agent.lower().replace('agent', '').strip() 
                for agent in team_agents
            ]

            # Valider le répertoire de mission
            mission_dir = config.get('mission_dir')
            if not mission_dir or not os.path.exists(mission_dir):
                raise ValueError(f"Invalid mission directory: {mission_dir}")

            # Initialiser chaque agent
            initialized_agents = {}
            for agent_name in normalized_agents:
                try:
                    # Configuration de l'agent
                    agent_config = {
                        'name': agent_name,
                        'mission_dir': mission_dir,
                        'prompt_file': os.path.join('prompts', f"{agent_name}.md")
                    }

                    # Créer l'agent
                    agent = self._create_dynamic_agent(agent_config)
                    if agent:
                        initialized_agents[agent_name] = agent
                        self.logger.log(f"Initialized agent: {agent_name}")

                except Exception as e:
                    self.logger.log(f"Error initializing agent {agent_name}: {str(e)}", 'error')

            self.agents = initialized_agents

        except Exception as e:
            self.logger.log(f"Critical error in agent initialization: {str(e)}", 'error')
            raise

    def _find_agent_prompt(self, agent_name: str, search_paths: List[str]) -> Optional[str]:
        """Diagnostic avancé pour trouver les fichiers de prompt avec logging détaillé"""
        normalized_name = agent_name.lower()
        
        potential_filenames = [
            f"{normalized_name}.md",
            f"{normalized_name}_agent.md", 
            f"agent_{normalized_name}.md",
            f"{normalized_name}.txt"
        ]

        searched_paths = []  # Track all paths searched

        for search_path in search_paths:
            if not os.path.exists(search_path):
                self.web_instance.log_message(
                    f"Search path does not exist: {search_path}", 
                    'warning'
                )
                continue

            for filename in potential_filenames:
                full_path = os.path.join(search_path, filename)
                searched_paths.append(full_path)
                
                self.web_instance.log_message(
                    f"Checking potential prompt file: {full_path}\n"
                    f"File exists: {os.path.exists(full_path)}", 
                    'debug'
                )

                if os.path.exists(full_path):
                    return full_path

        # Log détaillé si aucun fichier n'est trouvé
        self.web_instance.log_message(
            f"No prompt file found for agent: {agent_name}\n"
            f"Searched paths: {searched_paths}\n"
            f"Potential filenames: {potential_filenames}", 
            'error'
        )
        return None

    def _read_prompt_file(self, prompt_file: str) -> Optional[str]:
        """
        Lit le contenu d'un fichier prompt avec gestion des erreurs
        
        Args:
            prompt_file: Chemin vers le fichier prompt
            
        Returns:
            str: Contenu du prompt ou None si erreur
        """
        try:
            if not prompt_file or not os.path.exists(prompt_file):
                self.web_instance.log_message(
                    f"Prompt file not found: {prompt_file}", 
                    'error'
                )
                return None
                
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if not content.strip():
                self.web_instance.log_message(
                    f"Empty prompt file: {prompt_file}", 
                    'warning'
                )
                return None
                
            self.web_instance.log_message(
                f"Successfully read prompt from: {prompt_file}", 
                'debug'
            )
            return content
            
        except Exception as e:
            self.web_instance.log_message(
                f"Error reading prompt file {prompt_file}: {str(e)}", 
                'error'
            )
            return None

    def _create_default_prompt(self, agent_name: str) -> str:
        """
        Crée un prompt par défaut pour un agent
        
        Args:
            agent_name: Nom de l'agent
            
        Returns:
            str: Prompt par défaut
        """
        default_prompt = f"""# {agent_name.capitalize()} Agent

## MISSION
Define the core mission and purpose of the {agent_name} agent.

## CONTEXT
Provide background information and context for the agent's operations.

## INSTRUCTIONS
Detailed step-by-step instructions for the agent's workflow.

## RULES
- Rule 1: Define key operational rules
- Rule 2: Specify constraints and limitations
- Rule 3: List required behaviors

## CONSTRAINTS
List any specific constraints or limitations.
"""
        
        self.web_instance.log_message(
            f"Created default prompt for {agent_name}", 
            'info'
        )
        
        return default_prompt

    def _find_prompt_file(self, agent_name: str) -> Optional[str]:
        """
        Find or create a prompt file for an agent
    
        Args:
            agent_name (str): Name of the agent
    
        Returns:
            Optional path to prompt file
        """
        try:
            # Normalize agent name
            normalized_name = agent_name.lower().replace('agent', '').strip()
        
            # Possible prompt locations
            prompt_locations = [
                PathManager.get_prompt_file(normalized_name),
                os.path.join(PathManager.get_prompts_path(), f"{normalized_name}.md"),
                os.path.join(PathManager.get_prompts_path(), "custom", f"{normalized_name}.md")
            ]
        
            # Try to find an existing prompt file
            for location in prompt_locations:
                if os.path.exists(location):
                    self.web_instance.log_message(f"Found prompt for {normalized_name}: {location}", 'debug')
                    return location
        
            # If no prompt found, create a default
            default_prompt_path = self._create_default_prompt_file(normalized_name)
        
            return default_prompt_path
    
        except Exception as e:
            self.web_instance.log_message(f"Error finding prompt for {agent_name}: {str(e)}", 'error')
            return None

    def _create_default_prompt_file(self, agent_name: str) -> Optional[str]:
        """Create a default prompt file if no existing file is found"""
        try:
            # Use custom prompts directory for new files
            custom_prompts_dir = PathManager.get_custom_prompts_path()
            os.makedirs(custom_prompts_dir, exist_ok=True)
            
            # Construct prompt file path
            prompt_path = os.path.join(custom_prompts_dir, f"{agent_name}.md")
            
            # Default prompt template
            default_content = f"""# {agent_name.capitalize()} Agent Prompt

## MISSION
Define the core mission and purpose of the {agent_name} agent.

## CONTEXT
Provide background information and context for the agent's operations.

## INSTRUCTIONS
Detailed step-by-step instructions for the agent's workflow.

## RULES
- Rule 1: 
- Rule 2: 
- Rule 3: 

## CONSTRAINTS
List any specific constraints or limitations.
"""
            
            # Write default prompt file
            with open(prompt_path, 'w', encoding='utf-8') as f:
                f.write(default_content)
            
            self.web_instance.log_message(f"Created default prompt file for {agent_name}: {prompt_path}", 'info')
            return prompt_path
        
        except Exception as e:
            self.web_instance.log_message(f"Error creating default prompt file for {agent_name}: {str(e)}", 'error')
            return None

    def get_available_agents(self) -> List[str]:
        """Get list of available agent names"""
        # If no agents, try to initialize
        if not self.agents:
            try:
                # Try to get agents from active team or use a default list
                team_agents = None
                try:
                    active_team = self.web_instance.team_service.active_team
                    team_agents = active_team['agents'] if active_team else None
                except Exception:
                    pass
            
                # Use a comprehensive default list if no team agents
                if not team_agents:
                    team_agents = [
                        'specifications',
                        'management',
                        'evaluation',
                        'chroniqueur',
                        'documentaliste',
                        'duplication',
                        'redacteur',
                        'validation',
                        'production',
                        'testeur'
                    ]
            
                self.init_agents({
                }, team_agents)
            except Exception as e:
                self.web_instance.log_message(f"Failed to initialize agents: {str(e)}", 'error')
    
        return list(self.agents.keys())

    def toggle_agent(self, agent_name: str, action: str, mission_dir: Optional[str] = None) -> bool:
        """Démarre ou arrête un agent"""
        try:
            agent_key = agent_name.lower().replace('agent', '').strip()
            
            # Obtenir l'agent
            agent = self.agents.get(agent_key)
            if not agent:
                self.logger.log(f"Agent {agent_name} not found", 'error')
                return False

            # Mettre à jour le répertoire de mission si fourni
            if mission_dir:
                agent.mission_dir = mission_dir

            # Exécuter l'action
            if action == 'start':
                if not agent.running:
                    agent.start()
                    # Créer et démarrer le thread
                    thread = threading.Thread(
                        target=self._run_agent_wrapper,
                        args=(agent_name, agent),
                        daemon=True
                    )
                    self.agent_threads[agent_name] = thread
                    thread.start()
                return agent.running
                
            elif action == 'stop':
                if agent.running:
                    agent.stop()
                return not agent.running

            return False

        except Exception as e:
            self.logger.log(f"Error in toggle_agent: {str(e)}", 'error')
            return False

    def _cleanup_cache(self, cache_type: str) -> None:
        """Centralized cache cleanup"""
        try:
            cache = self._get_cache(cache_type)
            now = time.time()
            expired = [
                key for key, (_, timestamp) in cache.items()
                if now - timestamp > self.ttl
            ]
            for key in expired:
                self._remove(key, cache_type)
        except Exception as e:
            self.logger.log(f"Cache cleanup error: {str(e)}", 'error')

    def _cleanup_resources(self):
        """Nettoie les ressources"""
        try:
            with self._cleanup_lock:
                # Nettoyer les threads
                for thread in self.agent_threads.values():
                    if thread and thread.is_alive():
                        try:
                            thread.join(timeout=1)
                        except:
                            pass
                            
                self.agent_threads.clear()
                
        except Exception as e:
            self.logger.log(f"Error cleaning up resources: {str(e)}", 'error')

    def start_all_agents(self) -> None:
        """Start all agents with better resource management"""
        try:
            self.web_instance.log_message("🚀 Starting agents...", 'info')
            
            # Check available agents
            available_agents = self.get_available_agents()
            self.web_instance.log_message(f"Available agents: {available_agents}", 'debug')
            
            if not available_agents:
                self.web_instance.log_message("No agents available to start", 'warning')
                return
                
            # Get current mission from FileManager and validate
            current_mission = self.web_instance.file_manager.current_mission
            if not current_mission:
                self.web_instance.log_message("❌ No mission selected - cannot start agents", 'error')
                return

            # Get mission directory using PathManager
            try:
                mission_dir = PathManager.get_mission_path(current_mission)
                self.web_instance.log_message(f"Using mission directory: {mission_dir}", 'info')
                
                # Validate mission directory
                if not os.path.exists(mission_dir):
                    raise ValueError(f"Mission directory not found: {mission_dir}")
                if not os.access(mission_dir, os.R_OK | os.W_OK):
                    raise ValueError(f"Insufficient permissions on: {mission_dir}")
                    
            except Exception as e:
                self.web_instance.log_message(f"❌ Invalid mission configuration: {str(e)}", 'error')
                return

            # Initialize agents if not already done
            if not self.agents:
                self.web_instance.log_message("Initializing agents...", 'info')
                config = {
                    'mission_dir': mission_dir
                }
                
                # Validate config before initialization
                if not self._validate_agent_config(config):
                    self.web_instance.log_message(
                        "Invalid configuration for agents, skipping initialization",
                        'error'
                    )
                    return
                    
                self.init_agents(config)
                
                if not self.agents:
                    self.web_instance.log_message("❌ Failed to initialize agents", 'error')
                    return

            # Update mission directory for all agents
            for name, agent in self.agents.items():
                agent.mission_dir = mission_dir
                self.web_instance.log_message(f"Set mission dir for {name}: {mission_dir}", 'debug')

            # Store thread references
            self.agent_threads = {}
            
            self.running = True
            
            # Start monitor thread
            self._start_monitor_thread()
            
            # Start agent threads
            for name, agent in self.agents.items():
                try:
                    self.web_instance.log_message(f"Starting agent: {name}", 'info')
                    agent.start()
                    
                    # Create and start thread
                    thread = threading.Thread(
                        target=self._run_agent_wrapper,
                        args=(name, agent),
                        daemon=True,
                        name=f"Agent-{name}"
                    )
                    
                    self.agent_threads[name] = thread
                    thread.start()
                    
                    self.web_instance.log_message(f"✅ Agent {name} started successfully", 'success')
                    
                except Exception as agent_error:
                    self.web_instance.log_message(
                        f"Failed to start agent {name}: {str(agent_error)}", 
                        'error'
                    )

            # Verify all threads are running
            running_threads = [name for name, thread in self.agent_threads.items() if thread.is_alive()]
            self.web_instance.log_message(f"Running agent threads: {running_threads}", 'info')

            if len(running_threads) != len(self.agents):
                self.web_instance.log_message(
                    f"⚠️ Only {len(running_threads)} of {len(self.agents)} agents started",
                    'warning'
                )
            else:
                self.web_instance.log_message("✨ All agents started successfully", 'success')

        except Exception as e:
            self.web_instance.log_message(
                f"Critical error starting agents:\n"
                f"Error: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}", 
                'critical'
            )
            raise

    def stop_all_agents(self) -> None:
        """Arrête tous les agents"""
        try:
            for name, agent in self.agents.items():
                try:
                    agent.stop()
                    self.logger.log(f"Stopped agent {name}")
                except Exception as e:
                    self.logger.log(f"Error stopping agent {name}: {str(e)}", 'error')

            self._cleanup_resources()
            
        except Exception as e:
            self.logger.log(f"Error stopping agents: {str(e)}", 'error')
            raise

    def _start_monitor_thread(self) -> None:
        """Start the agent monitor thread if not running"""
        if not self.monitor_thread or not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(
                target=self._monitor_agents,
                daemon=True,
                name="AgentMonitor"
            )
            self.monitor_thread.start()

    def _calculate_system_health(self, metrics: Dict) -> float:
        """
        Calculate overall system health score from metrics
        
        Args:
            metrics: Dictionary containing system metrics
            
        Returns:
            float: Health score between 0.0 and 1.0
        """
        try:
            # Calculate base health score from agent states
            if metrics['total_agents'] == 0:
                return 0.0
                
            # Weight different factors
            agent_health = metrics['healthy_agents'] / metrics['total_agents']
            active_ratio = metrics['active_agents'] / metrics['total_agents']
            
            # Calculate error rate
            total_operations = (metrics['cache_hits'] + metrics['cache_misses'] + 
                              metrics['file_operations']['reads'] + 
                              metrics['file_operations']['writes'])
            error_rate = metrics['error_count'] / max(total_operations, 1)
            
            # Calculate cache performance
            cache_rate = metrics['cache_hits'] / max(metrics['cache_hits'] + metrics['cache_misses'], 1)
            
            # Weighted average of health indicators
            weights = {
                'agent_health': 0.4,
                'active_ratio': 0.3,
                'error_rate': 0.2,
                'cache_rate': 0.1
            }
            
            health_score = (
                weights['agent_health'] * agent_health +
                weights['active_ratio'] * active_ratio +
                weights['error_rate'] * (1 - error_rate) +  # Invert error rate
                weights['cache_rate'] * cache_rate
            )
            
            return max(0.0, min(1.0, health_score))  # Clamp between 0 and 1
            
        except Exception as e:
            self.web_instance.log_message(f"Error calculating system health: {str(e)}", 'error')
            return 0.0  # Return 0 on error

    def _handle_system_degradation(self, system_metrics: Dict) -> None:
        """Handle system-wide performance degradation"""
        try:
            # Log detailed metrics
            self.web_instance.log_message(
                f"System health degraded. Metrics:\n"
                f"- Active agents: {system_metrics['active_agents']}/{system_metrics['total_agents']}\n"
                f"- Healthy agents: {system_metrics['healthy_agents']}/{system_metrics['total_agents']}\n"
                f"- Error count: {system_metrics['error_count']}\n"
                f"- Cache performance: {system_metrics['cache_hits']}/{system_metrics['cache_hits'] + system_metrics['cache_misses']} hits",
                'warning'
            )

            # Attempt recovery actions
            recovery_actions = []

            # Check for unhealthy agents
            if system_metrics['healthy_agents'] < system_metrics['total_agents']:
                recovery_actions.append("Restarting unhealthy agents")
                for name, agent in self.agents.items():
                    if hasattr(agent, 'is_healthy') and not agent.is_healthy():
                        self._restart_agent(name, agent)

            # Check cache performance
            total_cache_ops = system_metrics['cache_hits'] + system_metrics['cache_misses']
            if total_cache_ops > 0:
                hit_rate = system_metrics['cache_hits'] / total_cache_ops
                if hit_rate < 0.7:  # Less than 70% hit rate
                    recovery_actions.append("Clearing and rebuilding caches")
                    for agent in self.agents.values():
                        if hasattr(agent, '_prompt_cache'):
                            agent._prompt_cache.clear()

            # Log recovery actions
            if recovery_actions:
                self.web_instance.log_message(
                    f"Recovery actions taken:\n- " + "\n- ".join(recovery_actions),
                    'info'
                )
            else:
                self.web_instance.log_message(
                    "No automatic recovery actions available for current degradation",
                    'warning'
                )

        except Exception as e:
            self.web_instance.log_message(
                f"Error handling system degradation: {str(e)}",
                'error'
            )

    def _monitor_agents(self) -> None:
        """Monitor agent status and health with enhanced metrics"""
        while self.running:
            try:
                status_updates = {}
                system_metrics = {
                    'total_agents': len(self.agents),
                    'active_agents': 0,
                    'healthy_agents': 0,
                    'error_count': 0,
                    'cache_hits': 0,
                    'cache_misses': 0,
                    'average_response_time': 0.0,
                    'memory_usage': {},
                    'file_operations': {
                        'reads': 0,
                        'writes': 0,
                        'errors': 0
                    }
                }

                # Monitor each agent
                for name, agent in self.agents.items():
                    try:
                        # Get detailed agent status
                        current_status = self._get_detailed_agent_status(name)
                        
                        # Update system metrics
                        if current_status['running']:
                            system_metrics['active_agents'] += 1
                        if current_status['health']['is_healthy']:
                            system_metrics['healthy_agents'] += 1
                            
                        # Aggregate performance metrics
                        system_metrics['cache_hits'] += current_status['metrics']['cache_hits']
                        system_metrics['cache_misses'] += current_status['metrics']['cache_misses']
                        system_metrics['file_operations']['reads'] += current_status['metrics']['file_reads']
                        system_metrics['file_operations']['writes'] += current_status['metrics']['file_writes']
                        
                        # Check for health issues
                        if not current_status['health']['is_healthy']:
                            self._handle_unhealthy_agent(name, current_status)
                            
                        status_updates[name] = current_status
                        
                    except Exception as agent_error:
                        system_metrics['error_count'] += 1
                        self._handle_agent_error(name, agent_error)

                # Calculate system health score
                health_score = self._calculate_system_health(system_metrics)
                
                # Update global status with metrics
                self._update_global_status(status_updates, system_metrics, health_score)
                
                # Handle system-wide issues
                if health_score < 0.7:  # Below 70% health
                    self._handle_system_degradation(system_metrics)
                    
            except Exception as e:
                self.web_instance.log_message(f"Error in monitor loop: {str(e)}", 'error')
            finally:
                time.sleep(30)  # Check every 30 seconds

    def get_agent_status(self, agent_name: str = None) -> Union[Dict[str, Dict[str, Any]], Dict[str, Any]]:
        """Get status for all agents or a specific agent"""
        if agent_name:
            # Normalize agent name
            agent_key = agent_name.lower()
            
            # Ensure agent exists
            if agent_key not in self.agents:
                return {
                    'running': False,
                    'status': 'not_initialized',
                    'error': f'Agent {agent_name} not initialized'
                }
            
            agent = self.agents[agent_key]
            
            return {
                'running': getattr(agent, 'running', False),
                'status': 'active' if getattr(agent, 'running', False) else 'inactive',
                'last_run': agent.last_run.isoformat() if hasattr(agent, 'last_run') and agent.last_run else None,
                'health': {
                    'is_healthy': agent.is_healthy() if hasattr(agent, 'is_healthy') else True,
                    'consecutive_no_changes': getattr(agent, 'consecutive_no_changes', 0)
                }
            }
        
        # If no specific agent, return status for all agents
        status = {}
        for name, agent in self.agents.items():
            name_lower = name.lower()
            status[name_lower] = {
                'running': agent.running,
                'status': 'active' if agent.running else 'inactive',
                'last_run': agent.last_run.isoformat() if agent.last_run else None,
                'last_change': agent.last_change.isoformat() if agent.last_change else None,
                'health': {
                    'is_healthy': agent.is_healthy(),
                    'consecutive_no_changes': agent.consecutive_no_changes,
                    'current_interval': agent.calculate_dynamic_interval()
                }
            }
        return status

    def _get_agent_status_details(self, agent) -> dict:
        """Get standardized agent status details"""
        return {
            'running': getattr(agent, 'running', False),
            'last_run': agent.last_run.isoformat() if hasattr(agent, 'last_run') and agent.last_run else None,
            'status': 'active' if getattr(agent, 'running', False) else 'inactive',
            'health': {
                'is_healthy': agent.is_healthy() if hasattr(agent, 'is_healthy') else True,
                'consecutive_no_changes': getattr(agent, 'consecutive_no_changes', 0)
            }
        }

    def _get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get status for a specific agent"""
        try:
            agent = self.agents.get(agent_name)
            if not agent:
                return self._get_agent_status_details(None)
                
            # Use relative paths for any internal API calls
            status_url = f"/api/agents/{agent_name}/status"
            return self._get_agent_status_details(agent)
            
        except Exception as e:
            self.web_instance.log_message(f"Error getting agent status: {str(e)}", 'error')
            return {
                'running': False,
                'status': 'error',
                'last_run': None,
                'health': {
                    'is_healthy': False,
                    'consecutive_no_changes': 0
                }
            }
    def _run_agent_wrapper(self, name: str, agent: 'KinOSAgent') -> None:
        """Wrapper pour exécuter un agent dans un thread"""
        try:
            self.logger.log(f"Starting agent {name}")
            agent.run()
        except Exception as e:
            self.logger.log(f"Agent {name} crashed: {str(e)}", 'error')
    def _get_detailed_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get comprehensive agent status including performance metrics"""
        try:
            agent = self.agents.get(agent_name)
            if not agent:
                return self._get_default_status()

            # Basic status
            status = {
                'running': agent.running,
                'status': 'active' if agent.running else 'inactive',
                'last_run': agent.last_run.isoformat() if agent.last_run else None,
                'last_change': agent.last_change.isoformat() if agent.last_change else None,
                
                # Health metrics
                'health': {
                    'is_healthy': agent.is_healthy(),
                    'consecutive_no_changes': agent.consecutive_no_changes,
                    'current_interval': agent.calculate_dynamic_interval(),
                    'error_rate': self._calculate_error_rate(agent),
                    'response_times': self._get_response_times(agent)
                },
                
                # Performance metrics
                'metrics': {
                    'cache_hits': getattr(agent, 'cache_hits', 0),
                    'cache_misses': getattr(agent, 'cache_misses', 0),
                    'file_reads': getattr(agent, 'file_reads', 0),
                    'file_writes': getattr(agent, 'file_writes', 0),
                    'average_processing_time': self._get_average_processing_time(agent),
                    'memory_usage': self._get_agent_memory_usage(agent)
                },
                
                # Resource utilization
                'resources': {
                    'cpu_usage': self._get_agent_cpu_usage(agent),
                    'memory_usage': self._get_agent_memory_usage(agent),
                    'file_handles': self._get_open_file_handles(agent)
                }
            }

            return status

        except Exception as e:
            self.web_instance.log_message(f"Error getting detailed status: {str(e)}", 'error')
            return self._get_default_status()

    def _calculate_error_rate(self, agent) -> float:
        """Calculate error rate for an agent over the last period"""
        try:
            # Get error count from last period (default to 0)
            error_count = getattr(agent, 'error_count', 0)
            total_runs = getattr(agent, 'total_runs', 1)  # Avoid division by zero
            
            # Calculate rate (0.0 to 1.0)
            return error_count / max(total_runs, 1)
            
        except Exception as e:
            self.web_instance.log_message(f"Error calculating error rate: {str(e)}", 'error')
            return 0.0

    def _handle_agent_error(self, agent_name: str, error: Exception) -> None:
        """Handle agent errors with recovery attempts"""
        try:
            self.web_instance.log_message(f"Agent {agent_name} error: {str(error)}", 'error')
            
            # Get agent instance
            agent = self.agents.get(agent_name)
            if not agent:
                return
                
            # Increment error count
            agent.error_count = getattr(agent, 'error_count', 0) + 1
            
            # Try to recover agent
            if hasattr(agent, 'recover_from_error'):
                try:
                    success = agent.recover_from_error()
                    if success:
                        self.web_instance.log_message(f"Agent {agent_name} recovered successfully", 'info')
                    else:
                        self.web_instance.log_message(f"Agent {agent_name} recovery failed", 'warning')
                except Exception as recovery_error:
                    self.web_instance.log_message(f"Error during agent recovery: {str(recovery_error)}", 'error')
            
            # Stop agent if too many errors
            if agent.error_count > 5:  # Configurable threshold
                self.web_instance.log_message(f"Stopping agent {agent_name} due to too many errors", 'warning')
                agent.stop()
                
        except Exception as e:
            self.web_instance.log_message(f"Error handling agent error: {str(e)}", 'error')

    def _get_response_times(self, agent) -> Dict[str, float]:
        """Get agent response time metrics"""
        return {
            'average': getattr(agent, 'avg_response_time', 0.0),
            'min': getattr(agent, 'min_response_time', 0.0),
            'max': getattr(agent, 'max_response_time', 0.0)
        }

    def _get_average_processing_time(self, agent) -> float:
        """Get average processing time for agent operations"""
        return getattr(agent, 'avg_processing_time', 0.0)

    def _get_agent_memory_usage(self, agent) -> Dict[str, int]:
        """Get memory usage metrics for an agent"""
        return {
            'current': getattr(agent, 'current_memory', 0),
            'peak': getattr(agent, 'peak_memory', 0)
        }

    def _get_agent_cpu_usage(self, agent) -> float:
        """Get CPU usage percentage for an agent"""
        return getattr(agent, 'cpu_usage', 0.0)

    def _get_open_file_handles(self, agent) -> int:
        """Get number of open file handles for an agent"""
        return getattr(agent, 'open_files', 0)

    def _get_default_status(self) -> Dict[str, Any]:
        """Get default status structure for agents"""
        return {
            'running': False,
            'status': 'inactive',
            'last_run': None,
            'last_change': None,
            'health': {
                'is_healthy': True,
                'consecutive_no_changes': 0,
                'current_interval': 60,
                'error_rate': 0.0,
                'response_times': {
                    'average': 0.0,
                    'min': 0.0,
                    'max': 0.0
                }
            },
            'metrics': {
                'cache_hits': 0,
                'cache_misses': 0,
                'file_reads': 0,
                'file_writes': 0,
                'average_processing_time': 0.0,
                'memory_usage': {
                    'current': 0,
                    'peak': 0
                }
            },
            'resources': {
                'cpu_usage': 0.0,
                'memory_usage': {
                    'current': 0,
                    'peak': 0
                },
                'file_handles': 0
            }
        }

    def _restart_agent(self, name: str, agent: 'KinOSAgent') -> None:
        """Safely restart a single agent"""
        try:
            # Stop the agent
            agent.stop()
            time.sleep(1)  # Brief pause
            
            # Start the agent
            agent.start()
            thread = threading.Thread(
                target=self._run_agent_wrapper,
                args=(name, agent),
                daemon=True,
                name=f"Agent-{name}"
            )
            thread.start()
            
            self.web_instance.log_message(f"Successfully restarted agent {name}", 'success')
            
        except Exception as e:
            self.web_instance.log_message(f"Error restarting agent {name}: {str(e)}", 'error')


    def _verify_team_agents(self, team_agents: List[str]) -> bool:
        """Vérifie que tous les agents requis sont disponibles"""
        try:
            available_agents = set(self.web_instance.agent_service.get_available_agents())
            normalized_agents = set(self._normalize_agent_names(team_agents))
            
            missing_agents = normalized_agents - available_agents
            if missing_agents:
                self.web_instance.log_message(
                    f"Missing required agents: {missing_agents}\n"
                    f"Available agents: {available_agents}", 
                    'error'
                )
                return False
            return True
        except Exception as e:
            self.web_instance.log_message(f"Error verifying team agents: {str(e)}", 'error')
            return False

    def _update_global_status(self, status_updates: Dict[str, Dict], system_metrics: Dict, health_score: float) -> None:
        """Update global system status based on agent states"""
        try:
            total_agents = len(status_updates)
            active_agents = sum(1 for status in status_updates.values() if status['running'])
            healthy_agents = sum(1 for status in status_updates.values() 
                               if status['health']['is_healthy'])
            
            system_status = {
                'total_agents': total_agents,
                'active_agents': active_agents,
                'healthy_agents': healthy_agents,
                'system_health': health_score,
                'metrics': system_metrics,
                'timestamp': datetime.now().isoformat(),
                'agents': status_updates
            }
            
            # Log significant changes
            if system_status['system_health'] < 0.8:  # Less than 80% healthy
                self.web_instance.log_message(
                    f"System health degraded: {system_status['system_health']:.1%}", 
                    'warning'
                )
                
            # Store status for API access
            self._last_status = system_status
            
        except Exception as e:
            self.web_instance.log_message(f"Error updating global status: {str(e)}", 'error')

    def create_agent(self, name: str, prompt: str) -> bool:
        """Create a new agent with the given name and prompt"""
        try:
            # Validate name
            if not validate_agent_name(name):
                raise ValueError("Invalid agent name format")

            # Validate prompt
            if not self._validate_prompt(prompt):
                raise ValueError("Invalid prompt content")

            # Use PathManager for custom prompts
            custom_prompts_dir = PathManager.get_custom_prompts_path()
            os.makedirs(custom_prompts_dir, exist_ok=True)
            
            # Check if agent already exists
            prompt_file = os.path.join(custom_prompts_dir, f'{name}.md')
            if os.path.exists(prompt_file):
                raise ValueError(f"Agent {name} already exists")

            # Backup existing prompts if any
            self._backup_prompt(name)

            # Save prompt file
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(prompt)

            # Reinitialize agent
            self.init_agents({
            }, [name])

            # Log agent creation
            self.log_agent_creation(name, True)
            return True

        except Exception as e:
            # Log agent creation failure
            self.log_agent_creation(name, False)
            self.web_instance.log_message(f"Error creating agent: {str(e)}", 'error')
            raise

    def get_agent_prompt(self, agent_id: str) -> Optional[str]:
        """Get the current prompt for a specific agent"""
        try:
            # Normalize agent name
            agent_name = agent_id.lower()
            
            # Use PathManager for prompts directory
            prompts_dir = PathManager.get_prompts_path()
            
            # Multiple possible prompt file locations
            possible_paths = [
                os.path.join(prompts_dir, f"{agent_name}.md"),
                os.path.join(prompts_dir, "custom", f"{agent_name}.md"),
                os.path.join(prompts_dir, f"{agent_name}_agent.md")
            ]
            
            # Try each possible path
            for prompt_path in possible_paths:
                if os.path.exists(prompt_path):
                    try:
                        with open(prompt_path, 'r', encoding='utf-8') as f:
                            prompt = f.read()
                        
                        # Validate prompt content
                        if prompt and prompt.strip():
                            self.web_instance.log_message(f"Retrieved prompt from {prompt_path}", 'debug')
                            return prompt
                    except Exception as read_error:
                        self.web_instance.log_message(f"Error reading prompt file {prompt_path}: {str(read_error)}", 'error')
            
            # If no prompt found, return a default
            default_prompt = f"""# {agent_name.capitalize()} Agent Default Prompt

## MISSION
Provide a default mission for the {agent_name} agent.

## CONTEXT
Default context for agent operations.

## INSTRUCTIONS
Default operational instructions.
"""
            self.web_instance.log_message(f"Using default prompt for {agent_name}", 'warning')
            return default_prompt
            
        except Exception as e:
            self.web_instance.log_message(f"Error getting agent prompt: {str(e)}", 'error')
            return None

    def save_agent_prompt(self, agent_id: str, prompt_content: str) -> bool:
        """Save updated prompt for a specific agent"""
        try:
            # Validate input
            if not prompt_content or not prompt_content.strip():
                raise ValueError("Prompt content cannot be empty")
            
            # Normalize agent name
            agent_name = agent_id.lower()
            
            # Use PathManager for custom prompts
            custom_prompts_dir = PathManager.get_custom_prompts_path()
            os.makedirs(custom_prompts_dir, exist_ok=True)
            
            # Construct prompt file path
            prompt_path = os.path.join(custom_prompts_dir, f"{agent_name}.md")
            
            # Write prompt file
            with open(prompt_path, 'w', encoding='utf-8') as f:
                f.write(prompt_content)
            
            # Reload agent if it exists
            if agent_name in self.agents:
                self.reload_agent(agent_name)
            
            self.web_instance.log_message(f"Saved new prompt for agent {agent_name}", 'success')
            return True
            
        except Exception as e:
            self.web_instance.log_message(f"Error saving agent prompt: {str(e)}", 'error')
            return False

    def _validate_prompt(self, prompt_content: str) -> bool:
        """Validate prompt content format and requirements"""
        try:
            if not prompt_content or not prompt_content.strip():
                return False
                
            # Vérifier la taille minimale
            if len(prompt_content) < 10:
                return False
                
            # Vérifier la présence d'instructions basiques
            required_elements = [
                "MISSION:",
                "CONTEXT:",
                "INSTRUCTIONS:",
                "RULES:"
            ]
            
            for element in required_elements:
                if element not in prompt_content:
                    self.web_instance.log_message(
                        f"Missing required element in prompt: {element}", 
                        'warning'
                    )
                    return False
                    
            return True
            
        except Exception as e:
            self.web_instance.log_message(f"Error validating prompt: {str(e)}", 'error')
            return False

    def _backup_prompt(self, agent_name: str) -> bool:
        """Create backup of current prompt before updating"""
        try:
            prompt_file = f"prompts/{agent_name}.md"
            if not os.path.exists(prompt_file):
                return True  # No backup needed
                
            # Create backups directory
            backup_dir = "prompts/backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{backup_dir}/{agent_name}_{timestamp}.md"
            
            # Copy current prompt to backup
            import shutil
            shutil.copy2(prompt_file, backup_file)
            
            self.web_instance.log_message(
                f"Created backup of {agent_name} prompt: {backup_file}", 
                'info'
            )
            return True
            
        except Exception as e:
            self.web_instance.log_message(f"Error backing up prompt: {str(e)}", 'error')
            return False

    def log_agent_creation(self, agent_name: str, success: bool):
        """Log agent creation events"""
        if success:
            self.logger.log(f"Successfully created agent: {agent_name}", 'success')
        else:
            self.logger.log(f"Failed to create agent: {agent_name}", 'error')

    def _load_prompt_template(self, agent_type: str) -> Optional[str]:
        """Load default prompt template for agent type"""
        try:
            template_file = f"templates/prompts/{agent_type}.md"
            if not os.path.exists(template_file):
                return None
                
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return content
            
        except Exception as e:
            self.web_instance.log_message(f"Error loading prompt template: {str(e)}", 'error')
            return None

    def _create_default_prompt(self, agent_name: str) -> str:
        """
        Create a default prompt for an agent
        
        Args:
            agent_name: Name of the agent
        
        Returns:
            str: Default prompt content
        """
        return f"""# {agent_name.capitalize()} Agent Default Prompt

## MISSION
Provide a comprehensive mission description for the {agent_name} agent.

## CONTEXT
Describe the operational context and key responsibilities.

## INSTRUCTIONS
1. Define primary objectives
2. Outline key operational guidelines
3. Specify decision-making criteria

## RULES
- Rule 1: Maintain clarity and precision
- Rule 2: Prioritize mission objectives
- Rule 3: Adapt to changing requirements

## CONSTRAINTS
- Adhere to ethical guidelines
- Maintain confidentiality
- Optimize resource utilization
"""
    def _diagnose_agent_initialization(self, agent_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Diagnostic détaillé de l'initialisation d'un agent"""
        diagnosis = {
            'agent_name': agent_name,
            'timestamp': datetime.now().isoformat(),
            'config_status': {
                'has_mission_dir': bool(config.get('mission_dir')),
                'mission_dir_exists': os.path.exists(config.get('mission_dir', '')),
                'mission_dir_writable': os.access(config.get('mission_dir', ''), os.W_OK)
            },
            'prompt_status': {
                'prompt_found': False,
                'prompt_path': None,
                'prompt_size': 0,
                'is_valid': False
            },
            'initialization_errors': []
        }
        
        try:
            # Vérifier le prompt
            prompt_file = self._find_agent_prompt(agent_name, [
                PathManager.get_prompts_path(),
                PathManager.get_custom_prompts_path()
            ])
            
            if prompt_file:
                diagnosis['prompt_status'].update({
                    'prompt_found': True,
                    'prompt_path': prompt_file,
                    'prompt_size': os.path.getsize(prompt_file),
                    'is_valid': True
                })
        except Exception as e:
            diagnosis['initialization_errors'].append(f"Prompt error: {str(e)}")
        
        return diagnosis

    def _validate_agent_config(self, config: Dict[str, Any]) -> bool:
        """Valide la configuration d'un agent"""
        required_fields = ['name', 'prompt']
        optional_fields = ['mission_dir']
        
        # Vérifier les champs requis
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            self.web_instance.log_message(
                f"Missing required fields in agent config: {missing_fields}", 
                'error'
            )
            return False
            
        # Vérifier le mission_dir si fourni
        if 'mission_dir' in config and config['mission_dir']:
            if not os.path.exists(config['mission_dir']):
                self.web_instance.log_message(
                    f"Mission directory does not exist: {config['mission_dir']}", 
                    'error'
                )
                return False
            
        return True

    def _create_dynamic_agent(self, config: Dict[str, Any]) -> Optional['KinOSAgent']:
        """Crée un agent à partir de sa configuration"""
        try:
            from aider_agent import AiderAgent
            return AiderAgent(config)
        except Exception as e:
            self.logger.log(f"Error creating agent: {str(e)}", 'error')
            return None
