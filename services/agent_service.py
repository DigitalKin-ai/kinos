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
from agents import (
    SpecificationsAgent,
    ProductionAgent,
    ManagementAgent,
    EvaluationAgent,
    SuiviAgent
)

class AgentService:
    def __init__(self, web_instance):
        self.web_instance = web_instance
        self.agents = {}
        self.monitor_thread = None
        self.running = False

    def init_agents(self, config: Dict[str, Any]) -> None:
        """Initialize all agents with configuration"""
        try:
            # Get current mission
            missions = self.web_instance.mission_service.get_all_missions()
            mission_name = missions[0]['name'] if missions else None
            
            if not mission_name:
                self.web_instance.log_message("No mission available for initialization")
                return

            # Base configuration for all agents
            base_config = {
                "check_interval": 10,
                "anthropic_api_key": config["anthropic_api_key"],
                "openai_api_key": config["openai_api_key"],
                "mission_name": mission_name
            }

            # Initialize each agent type
            self.agents = {
                "Specification": SpecificationsAgent({**base_config, "name": "Specification"}),
                "Production": ProductionAgent({**base_config, "name": "Production"}),
                "Management": ManagementAgent({**base_config, "name": "Management"}),
                "Evaluation": EvaluationAgent({**base_config, "name": "Evaluation"}),
                "Suivi": SuiviAgent({**base_config, "name": "Suivi"})
            }

        except Exception as e:
            self.web_instance.log_message(f"Error initializing agents: {str(e)}", level='error')
            raise

    def start_all_agents(self) -> None:
        """Start all agents"""
        try:
            self.running = True
            
            # Start monitor thread
            if not self.monitor_thread or not self.monitor_thread.is_alive():
                self.monitor_thread = threading.Thread(
                    target=self._monitor_agents,
                    daemon=True,
                    name="AgentMonitor"
                )
                self.monitor_thread.start()
            
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
                except Exception as e:
                    self.web_instance.log_message(f"Error starting agent {name}: {str(e)}", level='error')

        except Exception as e:
            self.web_instance.log_message(f"Error starting agents: {str(e)}", level='error')
            raise

    def stop_all_agents(self) -> None:
        """Stop all agents"""
        try:
            self.running = False
            
            # Stop each agent
            for name, agent in self.agents.items():
                try:
                    agent.stop()
                except Exception as e:
                    self.web_instance.log_message(f"Error stopping agent {name}: {str(e)}", level='error')
            
            # Stop monitor thread
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2)

        except Exception as e:
            self.web_instance.log_message(f"Error stopping agents: {str(e)}", level='error')
            raise

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
        """Get status of all agents"""
        return {
            name.lower(): {
                'running': agent.running,
                'last_run': agent.last_run.isoformat() if agent.last_run else None,
                'last_change': agent.last_change.isoformat() if agent.last_change else None
            }
            for name, agent in self.agents.items()
        }
