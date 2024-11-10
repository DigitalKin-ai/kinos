import os
import time
import threading
from typing import Dict, Any

class AgentService:
    def __init__(self, web_instance):
        self.web_instance = web_instance
        self.monitor_thread = None

    def start_agents(self):
        """Start all agents"""
        try:
            self.web_instance.log_message("🚀 Démarrage des agents...", level='info')
            self.web_instance.running = True
            
            # Start monitor thread
            self._start_monitor_thread()
            
            # Start individual agents
            self._start_individual_agents()
            
            self.web_instance.log_message("✨ Tous les agents sont actifs", level='success')
            
        except Exception as e:
            self.web_instance.log_message(f"❌ Erreur globale: {str(e)}", level='error')
            raise

    def update_agent_paths(self, mission_name: str) -> None:
        """Update file paths for all agents when mission changes without creating files"""
        try:
            # Explicit verification
            if self.web_instance.file_manager.current_mission != mission_name:
                self.web_instance.logger.log(
                    f"Mission mismatch - FileManager: {self.web_instance.file_manager.current_mission}, "
                    f"Requested: {mission_name}",
                    level='error'
                )
                # Force update
                self.web_instance.file_manager.current_mission = mission_name
            
            # Stop all agents
            self.stop_all_agents()
            
            # Build mission path - only verify directory exists
            mission_dir = os.path.abspath(os.path.join("missions", mission_name))
            if not os.path.exists(mission_dir):
                self.web_instance.logger.log(f"Mission directory not found: {mission_dir}", level='warning')
            
            self.web_instance.logger.log(f"Updating agent paths for mission: {mission_name}", level='debug')

            # Track agent states
            was_running = any(agent.running for agent in self.agents.values())
                    
            # Restart agents if they were running
            if was_running:
                self.start_all_agents()
                
            self.web_instance.logger.log(f"✓ Agent paths updated for mission: {mission_name}", level='success')
            
        except Exception as e:
            self.web_instance.logger.log(f"❌ Error updating agent paths: {str(e)}", level='error')
            raise

    def stop_agents(self):
        """Stop all agents"""
        try:
            self.web_instance.running = False
            self._stop_individual_agents()
            self._stop_monitor_thread()
            self.web_instance.log_message("All agents stopped", level='success')
        except Exception as e:
            self.web_instance.log_message(f"Error stopping agents: {str(e)}", level='error')
            raise

    def _start_monitor_thread(self):
        if not self.monitor_thread or not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(
                target=self.web_instance.monitor_agents,
                daemon=True,
                name="AgentMonitor"
            )
            self.monitor_thread.start()

    def _start_individual_agents(self):
        for name, agent in self.web_instance.agents.items():
            try:
                agent.start()
                thread = threading.Thread(
                    target=agent.run,
                    daemon=True,
                    name=f"Agent-{name}"
                )
                thread.start()
                self.web_instance.log_message(f"✓ Agent {name} démarré", level='success')
            except Exception as e:
                self.web_instance.log_message(f"❌ Erreur démarrage agent {name}: {str(e)}", level='error')

    def _stop_individual_agents(self):
        for name, agent in self.web_instance.agents.items():
            try:
                agent.stop()
                self.web_instance.log_message(f"Agent {name} stopped", level='info')
            except Exception as e:
                self.web_instance.log_message(f"Error stopping agent {name}: {str(e)}", level='error')

    def _stop_monitor_thread(self):
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
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
    RedacteurAgent
)

class AgentService:
    def __init__(self, web_instance):
        self.web_instance = web_instance
        self.agents = {}
        self.monitor_thread = None
        self.running = False
        self.pending_agents = []  # Track agents waiting for file creation

    def init_agents(self, config: Dict[str, Any]) -> None:
        """Initialize all agents with configuration"""
        try:
            # Get current mission
            missions = self.web_instance.mission_service.get_all_missions()
            mission_name = missions[0]['name'] if missions else None
            
            if not mission_name:
                self.web_instance.log_message("No mission available for initialization")
                return

            # Construct mission directory path
            mission_dir = os.path.join("missions", mission_name)
            
            # Load prompts from files
            def load_prompt(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    self.web_instance.log_message(f"Error loading prompt from {file_path}: {e}", level='error')
                    return ""

            # Base configuration for all agents
            base_config = {
                "check_interval": 100,
                "anthropic_api_key": config["anthropic_api_key"],
                "openai_api_key": config["openai_api_key"],
                "mission_name": mission_name,
                "logger": self.web_instance.log_message,
                "web_instance": self.web_instance,  # Add web_instance to base config
                "mission_dir": mission_dir  # Add mission directory instead of file_path
            }

            # Initialize each agent type with relative paths
            self.agents = {
                "Specification": SpecificationsAgent({
                    **base_config,
                    "name": "Specification",
                    "prompt": load_prompt("prompts/specifications.md"),
                    "prompt_file": "prompts/specifications.md"
                }),
                "Production": ProductionAgent({
                    **base_config,
                    "name": "Production",
                    "prompt": load_prompt("prompts/production.md"),
                    "prompt_file": "prompts/production.md"
                }),
                "Management": ManagementAgent({
                    **base_config,
                    "name": "Management",
                    "prompt": load_prompt("prompts/management.md"),
                    "prompt_file": "prompts/management.md"
                }),
                "Evaluation": EvaluationAgent({
                    **base_config,
                    "name": "Evaluation",
                    "prompt": load_prompt("prompts/evaluation.md"),
                    "prompt_file": "prompts/evaluation.md"
                }),
                "Suivi": SuiviAgent({
                    **base_config,
                    "name": "Suivi",
                    "prompt": load_prompt("prompts/suivi.md"),
                    "prompt_file": "prompts/suivi.md"
                }),
                "Documentaliste": DocumentalisteAgent({
                    **base_config,
                    "name": "Documentaliste", 
                    "prompt": load_prompt("prompts/documentaliste.md"),
                    "prompt_file": "prompts/documentaliste.md"
                }),
                "Duplication": DuplicationAgent({
                    **base_config,
                    "name": "Duplication",
                    "prompt": load_prompt("prompts/duplication.md"),
                    "prompt_file": "prompts/duplication.md"
                }),
                "Testeur": TesteurAgent({
                    **base_config,
                    "name": "Testeur",
                    "prompt": load_prompt("prompts/testeur.md"),
                    "prompt_file": "prompts/testeur.md"
                }),
                "Redacteur": RedacteurAgent({
                    **base_config,
                    "name": "Redacteur",
                    "prompt": load_prompt("prompts/redacteur.md"),
                    "prompt_file": "prompts/redacteur.md"
                })
            }

            # Log successful initialization
            self.web_instance.log_message("All agents initialized successfully", level='success')
            for name in self.agents:
                self.web_instance.log_message(f"Agent {name} ready", level='info')

        except Exception as e:
            self.web_instance.log_message(f"Error initializing agents: {str(e)}", level='error')
            raise

    def start_all_agents(self) -> None:
        """Start all agents"""
        try:
            self.web_instance.log_message("🚀 Starting agents...", level='info')
            self.running = True
            
            # Start monitor thread
            self._start_monitor_thread()
            
            # Start each agent
            for name, agent in self.agents.items():
                try:
                    agent.start()
                    thread = threading.Thread(
                        target=agent.run,
                        daemon=True,
                        name=f"Agent-{name}"
                    )
                    thread.start()
                    self.web_instance.log_message(f"✓ Agent {name} started", level='success')
                except Exception as e:
                    self.web_instance.log_message(f"Error starting agent {name}: {str(e)}", level='error')

            self.web_instance.log_message("✨ All agents active", level='success')
            
        except Exception as e:
            self.web_instance.log_message(f"Error starting agents: {str(e)}", level='error')
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
