import os
import time
import threading
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional
from utils.exceptions import AgentError
from agents.kinos_agent import KinOSAgent
import importlib
import inspect
from agents.kinos_agent import KinOSAgent

# Import agent types dynamically
agent_types_module = importlib.import_module('agents.agent_types')
agent_classes = {
    name: cls for name, cls in inspect.getmembers(agent_types_module)
    if (inspect.isclass(cls) and 
        issubclass(cls, KinOSAgent) and 
        cls != KinOSAgent)
}

class AgentService:
    def __init__(self, web_instance):
        self.web_instance = web_instance
        self.agents = {}
        self.monitor_thread = None
        self.running = False
        self.pending_agents = []  # Track agents waiting for file creation

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

    def _discover_agents(self) -> List[Dict[str, str]]:
        """Discover available agents by scanning prompts directory"""
        discovered_agents = []
        prompts_dir = "prompts"
        
        try:
            # Create prompts directory if it doesn't exist
            if not os.path.exists(prompts_dir):
                os.makedirs(prompts_dir)
                self.web_instance.log_message("Created prompts directory", level='info')
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
                        self.web_instance.log_message(f"Discovered agent: {agent_name}", level='debug')

            return discovered_agents

        except Exception as e:
            self.web_instance.log_message(f"Error discovering agents: {str(e)}", level='error')
            return []

    def _get_agent_class(self, agent_name: str):
        """Get the appropriate agent class based on name"""
        try:
            # Import the AiderAgent class dynamically
            from aider_agent import AiderAgent
            
            # All agents use AiderAgent as base class
            return AiderAgent
            
        except ImportError as e:
            self.web_instance.log_message(f"Error importing agent class: {str(e)}", level='error')
            return None

    def init_agents(self, config: Dict[str, Any]) -> None:
        """Initialize all agents with configuration"""
        try:
            # Verify config contains required API keys
            if not config.get("anthropic_api_key") or not config.get("openai_api_key"):
                raise ValueError("Missing required API keys in configuration")

            # Get current mission from FileManager - allow None initially
            current_mission = getattr(self.web_instance.file_manager, 'current_mission', None)

            # Base configuration for all agents
            base_config = {
                "check_interval": 100,
                "anthropic_api_key": config["anthropic_api_key"],
                "openai_api_key": config["openai_api_key"],
                "logger": self.web_instance.log_message,
                "web_instance": self.web_instance,
                "mission_dir": "missions",  # Default to missions directory
                "mission_name": "default"   # Default mission name
            }

            # Update config if mission is selected
            if current_mission:
                mission_dir = os.path.abspath(os.path.join("missions", current_mission))
                if os.path.exists(mission_dir) and os.access(mission_dir, os.R_OK | os.W_OK):
                    base_config.update({
                        "mission_dir": mission_dir,
                        "mission_name": current_mission
                    })

            self.web_instance.log_message(f"Initializing agents for mission: {current_mission}", level='info')

            # Discover available agents
            discovered_agents = self._discover_agents()
            if not discovered_agents:
                self.web_instance.log_message("No agents discovered in prompts directory", level='warning')
                return

            # Initialize each discovered agent
            self.agents = {}
            successful_inits = 0

            for agent_info in discovered_agents:
                try:
                    name = agent_info['name']
                    prompt_path = os.path.join("prompts", agent_info['prompt_file'])
                    agent_class = agent_info['class']

                    # Read prompt content
                    with open(prompt_path, 'r', encoding='utf-8') as f:
                        prompt = f.read()

                    agent_config = {
                        **base_config,
                        "name": name,
                        "prompt": prompt,
                        "prompt_file": prompt_path,
                        "is_active": False  # Agents start inactive without mission
                    }
                    
                    self.agents[name] = agent_class(agent_config)
                    successful_inits += 1
                    self.web_instance.log_message(f"✓ Agent {name} initialized (inactive)", level='success')
                    
                except Exception as e:
                    self.web_instance.log_message(f"Failed to initialize {name} agent: {str(e)}", level='error')
                    continue

            if successful_inits == 0:
                self.web_instance.log_message("Warning: No agents were successfully initialized", level='warning')
                return {}

            self.web_instance.log_message(f"Successfully initialized {successful_inits} agents", level='success')
            return self.agents

        except Exception as e:
            self.web_instance.log_message(f"Error initializing agents: {str(e)}", level='error')
            raise

    def get_available_agents(self) -> List[str]:
        """Get list of available agent names"""
        return list(self.agents.keys())

    def start_all_agents(self) -> None:
        """Start all agents"""
        try:
            self.web_instance.log_message("🚀 Starting agents...", level='info')
            
            # Check available agents
            available_agents = self.get_available_agents()
            self.web_instance.log_message(f"Available agents: {available_agents}", level='debug')
            
            if not available_agents:
                self.web_instance.log_message("No agents available to start", level='warning')
                return
                
            # Get current mission from FileManager
            current_mission = self.web_instance.file_manager.current_mission
            if not current_mission:
                raise AgentError("No current mission set")

            # Initialize agents if not already done
            if not self.agents:
                self.web_instance.log_message("Initializing agents...", level='info')
                self.init_agents({
                    "anthropic_api_key": self.web_instance.config["anthropic_api_key"],
                    "openai_api_key": self.web_instance.config["openai_api_key"]
                })
                
                if not self.agents:
                    raise AgentError("Failed to initialize agents")

            # Get absolute path to project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            mission_dir = os.path.abspath(os.path.join(project_root, "missions", current_mission))
            
            self.web_instance.log_message(f"Using absolute mission path: {mission_dir}", level='debug')
                
            # Verify directory exists and is accessible
            if not os.path.exists(mission_dir):
                raise AgentError(f"Mission directory not found: {mission_dir}")
            if not os.access(mission_dir, os.R_OK | os.W_OK):
                raise AgentError(f"Insufficient permissions on: {mission_dir}")

            # Store thread references
            self.agent_threads = {}

            # Log agents to be started
            self.web_instance.log_message(f"Agents to start: {list(self.agents.keys())}", level='debug')

            # Update mission directory for all agents
            for name, agent in self.agents.items():
                agent.mission_dir = mission_dir
                self.web_instance.log_message(f"Set mission dir for {name}: {mission_dir}", level='debug')
                
            self.running = True
            
            # Start monitor thread
            self._start_monitor_thread()
            
            # Start each agent in a new thread
            for name, agent in self.agents.items():
                try:
                    self.web_instance.log_message(f"Starting agent {name}...", level='debug')
                    
                    # Initialize agent
                    agent.start()
                    self.web_instance.log_message(f"Agent {name} initialized", level='debug')
                    
                    # Create thread
                    thread = threading.Thread(
                        target=self._run_agent_wrapper,  # Use wrapper function
                        args=(name, agent),
                        daemon=True,
                        name=f"Agent-{name}"
                    )
                    
                    # Store thread reference
                    self.agent_threads[name] = thread
                    
                    # Start thread
                    thread.start()
                    self.web_instance.log_message(f"Started thread for {name}", level='debug')

                    # Verify thread started
                    if not thread.is_alive():
                        raise AgentError(f"Thread failed to start for agent {name}")
                        
                    self.web_instance.log_message(f"✓ Agent {name} thread confirmed running", level='success')
                    
                except Exception as e:
                    self.web_instance.log_message(
                        f"Error starting agent {name}: {str(e)}\n{traceback.format_exc()}", 
                        level='error'
                    )

            # Verify all threads are running
            running_threads = [name for name, thread in self.agent_threads.items() if thread.is_alive()]
            self.web_instance.log_message(f"Running agent threads: {running_threads}", level='debug')

            if len(running_threads) != len(self.agents):
                raise AgentError(f"Only {len(running_threads)} of {len(self.agents)} agents started")

            self.web_instance.log_message("✨ All agents active", level='success')
            
        except Exception as e:
            self.web_instance.log_message(
                f"Error starting agents: {str(e)}\n{traceback.format_exc()}", 
                level='error'
            )
            raise

    def stop_all_agents(self) -> None:
        """Stop all agents and monitor thread"""
        try:
            self.running = False
            
            # Stop each agent
            for name, agent in self.agents.items():
                try:
                    agent.stop()
                    self.web_instance.log_message(f"Agent {name} stopped", level='info')
                except Exception as e:
                    self.web_instance.log_message(f"Error stopping agent {name}: {str(e)}", level='error')
            
            # Stop monitor thread
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2)

            self.web_instance.log_message("All agents stopped", level='success')
            
        except Exception as e:
            self.web_instance.log_message(f"Error stopping agents: {str(e)}", level='error')
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
                self.web_instance.log_message(f"Error in monitor loop: {str(e)}", level='error')
            finally:
                time.sleep(30)  # Check every 30 seconds

    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents including health metrics"""
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

    def _get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get status for a specific agent"""
        try:
            agent = self.agents.get(agent_name)
            if not agent:
                return {
                    'running': False,
                    'status': 'inactive',
                    'last_run': None,
                    'health': {
                        'is_healthy': True,
                        'consecutive_no_changes': 0
                    }
                }
                
            return {
                'running': agent.running,
                'status': 'active' if agent.running else 'inactive',
                'last_run': agent.last_run.isoformat() if agent.last_run else None,
                'health': {
                    'is_healthy': agent.is_healthy(),
                    'consecutive_no_changes': getattr(agent, 'consecutive_no_changes', 0)
                }
            }
            
        except Exception as e:
            self.web_instance.log_message(f"Error getting agent status: {str(e)}", level='error')
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
        """Wrapper function to catch any exceptions from agent run method"""
        try:
            self.web_instance.log_message(f"Agent {name} thread starting run method", level='debug')
            agent.run()
        except Exception as e:
            self.web_instance.log_message(
                f"Agent {name} thread crashed: {str(e)}\n{traceback.format_exc()}", 
                level='error'
            )
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
            self.web_instance.log_message(f"Error getting detailed status: {str(e)}", level='error')
            return self._get_default_status()

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
            
            self.web_instance.log_message(f"Successfully restarted agent {name}", level='success')
            
        except Exception as e:
            self.web_instance.log_message(f"Error restarting agent {name}: {str(e)}", level='error')

    def _update_global_status(self, status_updates: Dict[str, Dict]) -> None:
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
                'system_health': healthy_agents / total_agents if total_agents > 0 else 0,
                'timestamp': datetime.now().isoformat(),
                'agents': status_updates
            }
            
            # Log significant changes
            if system_status['system_health'] < 0.8:  # Less than 80% healthy
                self.web_instance.log_message(
                    f"System health degraded: {system_status['system_health']:.1%}", 
                    level='warning'
                )
                
            # Store status for API access
            self._last_status = system_status
            
        except Exception as e:
            self.web_instance.log_message(f"Error updating global status: {str(e)}", level='error')

    def get_agent_prompt(self, agent_id: str) -> Optional[str]:
        """Get the current prompt for a specific agent"""
        try:
            agent_name = agent_id.lower()
            if agent_name not in self.agents:
                self.web_instance.log_message(f"Agent {agent_id} not found", level='error')
                return None
                
            agent = self.agents[agent_name]
            prompt = agent.get_prompt()
            
            # Log prompt access
            self.web_instance.log_message(f"Retrieved prompt for agent {agent_name}", level='debug')
            return prompt
            
        except Exception as e:
            self.web_instance.log_message(f"Error getting agent prompt: {str(e)}", level='error')
            return None

    def save_agent_prompt(self, agent_id: str, prompt_content: str) -> bool:
        """Save updated prompt for a specific agent"""
        try:
            agent_name = agent_id.lower()
            if agent_name not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
                
            if not prompt_content or not prompt_content.strip():
                raise ValueError("Prompt content cannot be empty")
                
            agent = self.agents[agent_name]
            
            # Ensure prompts directory exists
            os.makedirs("prompts", exist_ok=True)
            
            # Save prompt to file
            prompt_file = f"prompts/{agent_name}.md"
            success = agent.save_prompt(prompt_content)
            
            if success:
                self.web_instance.log_message(f"Saved new prompt for agent {agent_name}", level='success')
                
                # Stop agent if running
                if agent.running:
                    agent.stop()
                    self.web_instance.log_message(f"Stopped agent {agent_name} for prompt update", level='info')
                    
                    # Restart agent with new prompt
                    agent.start()
                    thread = threading.Thread(
                        target=self._run_agent_wrapper,
                        args=(agent_name, agent),
                        daemon=True,
                        name=f"Agent-{agent_name}"
                    )
                    thread.start()
                    self.web_instance.log_message(f"Restarted agent {agent_name} with new prompt", level='success')
                    
            return success
            
        except Exception as e:
            self.web_instance.log_message(f"Error saving agent prompt: {str(e)}", level='error')
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
                        level='warning'
                    )
                    return False
                    
            return True
            
        except Exception as e:
            self.web_instance.log_message(f"Error validating prompt: {str(e)}", level='error')
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
                level='info'
            )
            return True
            
        except Exception as e:
            self.web_instance.log_message(f"Error backing up prompt: {str(e)}", level='error')
            return False

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
            self.web_instance.log_message(f"Error loading prompt template: {str(e)}", level='error')
            return None
