import threading
from datetime import datetime
from typing import Dict, Any
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

    def init_agents(self, config: Dict[str, Any]) -> None:
        """Initialize all agents with configuration"""
        try:
            # Verify config contains required API keys
            if not config.get("anthropic_api_key") or not config.get("openai_api_key"):
                raise ValueError("Missing required API keys in configuration")

            # Get current mission from FileManager
            current_mission = self.web_instance.file_manager.current_mission
            if not current_mission:
                raise ValueError("No current mission set")

            # Setup mission directory
            mission_dir = os.path.join("missions", current_mission)
            if not os.path.exists(mission_dir) or not os.access(mission_dir, os.R_OK | os.W_OK):
                raise ValueError(f"Mission directory not accessible: {mission_dir}")

            if not os.path.exists("prompts"):
                raise ValueError("Prompts directory not found")

            self.web_instance.log_message(f"Initializing agents for mission: {current_mission}", level='info')

            # Base configuration for all agents
            base_config = {
                "check_interval": 100,
                "anthropic_api_key": config["anthropic_api_key"],
                "openai_api_key": config["openai_api_key"],
                "mission_name": current_mission,
                "logger": self.web_instance.log_message,
                "web_instance": self.web_instance,
                "mission_dir": mission_dir
            }

            # Initialize each agent type
            self.agents = {}
            agent_configs = [
                ("Specification", SpecificationsAgent, "specifications.md"),
                ("Production", ProductionAgent, "production.md"),
                ("Management", ManagementAgent, "management.md"),
                ("Evaluation", EvaluationAgent, "evaluation.md"),
                ("Suivi", SuiviAgent, "suivi.md"),
                ("Documentaliste", DocumentalisteAgent, "documentaliste.md"),
                ("Duplication", DuplicationAgent, "duplication.md"),
                ("Testeur", TesteurAgent, "testeur.md"),
                ("Validation", ValidationAgent, "validation.md"),
                ("Redacteur", RedacteurAgent, "redacteur.md")
            ]

            successful_inits = 0
            for name, agent_class, prompt_file in agent_configs:
                try:
                    prompt_path = os.path.join("prompts", prompt_file)
                    if not os.path.exists(prompt_path):
                        self.web_instance.log_message(f"Prompt file not found: {prompt_path}", level='error')
                        continue

                    with open(prompt_path, 'r', encoding='utf-8') as f:
                        prompt = f.read()

                    agent_config = {
                        **base_config,
                        "name": name,
                        "prompt": prompt,
                        "prompt_file": prompt_path
                    }
                    
                    self.agents[name] = agent_class(agent_config)
                    successful_inits += 1
                    self.web_instance.log_message(f"✓ Agent {name} initialized", level='success')
                    
                except Exception as e:
                    self.web_instance.log_message(f"Failed to initialize {name} agent: {str(e)}", level='error')

            if successful_inits == 0:
                raise ValueError("No agents were successfully initialized")

            self.web_instance.log_message(f"Successfully initialized {successful_inits} agents", level='success')

        except Exception as e:
            self.web_instance.log_message(f"Error initializing agents: {str(e)}", level='error')
            raise

    def start_all_agents(self) -> None:
        """Start all agents"""
        try:
            self.web_instance.log_message("🚀 Starting agents...", level='info')
            
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
                for name, agent in self.agents.items():
                    if not agent.is_healthy():
                        self.web_instance.log_message(f"Agent {name} appears unhealthy", level='warning')
                        # Implement recovery logic here
            except Exception as e:
                self.web_instance.log_message(f"Error monitoring agents: {str(e)}", level='error')
            finally:
                time.sleep(30)  # Check every 30 seconds

    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents including pending state"""
        status = {}
        for name, agent in self.agents.items():
            name_lower = name.lower()
            if name in getattr(self, 'pending_agents', []):
                status[name_lower] = {
                    'running': False,
                    'pending': True,
                    'status': 'waiting_for_file',
                    'last_run': None,
                    'last_change': None
                }
            else:
                status[name_lower] = {
                    'running': agent.running,
                    'pending': False,
                    'status': 'active',
                    'last_run': agent.last_run.isoformat() if agent.last_run else None,
                    'last_change': agent.last_change.isoformat() if agent.last_change else None
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
