import os
import time
import threading
import traceback
from datetime import datetime
from typing import Dict, Any, List
from utils.exceptions import AgentError
from agents.kinos_agent import KinOSAgent
from agents.agent_types import (
    SpecificationsAgent,
    ProductionAgent,
    ManagementAgent,
    EvaluationAgent,
    SuiviAgent,
    DocumentalisteAgent,
    DuplicationAgent,
    TesteurAgent,
    ValidationAgent,
    RedacteurAgent
)

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
        # Map of agent names to their classes
        agent_classes = {
            'validation': ValidationAgent,
            'specifications': SpecificationsAgent,
            'production': ProductionAgent,
            'management': ManagementAgent,
            'evaluation': EvaluationAgent,
            'suivi': SuiviAgent,
            'documentaliste': DocumentalisteAgent,
            'duplication': DuplicationAgent,
            'testeur': TesteurAgent,
            'redacteur': RedacteurAgent
        }
        
        return agent_classes.get(agent_name.lower())

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
        """Monitor agent status and health"""
        while self.running:
            try:
                status_updates = {}
                for name, agent in self.agents.items():
                    try:
                        current_status = self._get_agent_status(name)
                        
                        # Check for health issues
                        if not current_status['health']['is_healthy']:
                            self.web_instance.log_message(
                                f"Agent {name} health check failed", 
                                level='warning'
                            )
                            
                            # Attempt recovery if needed
                            if agent.running and not agent.recover_from_error():
                                self.web_instance.log_message(
                                    f"Agent {name} recovery failed - restarting", 
                                    level='warning'
                                )
                                self._restart_agent(name, agent)
                                
                        status_updates[name] = current_status
                        
                    except Exception as agent_error:
                        self.web_instance.log_message(
                            f"Error monitoring agent {name}: {str(agent_error)}", 
                            level='error'
                        )
                        
                # Update global status
                self._update_global_status(status_updates)
                
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
    def _get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get detailed status information for an agent"""
        try:
            agent = self.agents.get(agent_name)
            if not agent:
                return {
                    'running': False,
                    'status': 'not_initialized',
                    'last_run': None,
                    'health': {
                        'is_healthy': False,
                        'consecutive_no_changes': 0,
                        'current_interval': None
                    }
                }

            return {
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

        except Exception as e:
            self.web_instance.log_message(f"Error getting agent status: {str(e)}", level='error')
            return {'running': False, 'status': 'error', 'error': str(e)}

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
