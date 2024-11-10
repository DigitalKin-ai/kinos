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
from utils.path_manager import PathManager

from agents.kinos_agent import KinOSAgent
from aider_agent import AiderAgent

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

    def init_agents(self, config: Dict[str, Any]) -> None:
        try:
            self.agents = {}
            
            # Get prompts directory using PathManager
            prompts_dir = PathManager.get_prompts_path()
            
            # Get current mission from FileManager if available
            current_mission = None
            if hasattr(self.web_instance.file_manager, 'current_mission'):
                current_mission = self.web_instance.file_manager.current_mission
            
            # Base configuration for all agents
            base_config = {
                **config,
                "web_instance": self.web_instance,
                "mission_name": current_mission or "_temp",  # Use _temp if no mission selected
                "mission_dir": os.path.join(PathManager.get_project_root(), "missions", current_mission or "_temp")
            }

            # Create temp mission dir if needed
            os.makedirs(base_config["mission_dir"], exist_ok=True)

            for file in os.listdir(prompts_dir):
                if file.endswith('.md'):
                    agent_name = file[:-3].lower()  # Remove .md extension
                    try:
                        with open(os.path.join(prompts_dir, file), 'r', encoding='utf-8') as f:
                            prompt_content = f.read()
                            
                        agent_config = {
                            **base_config,
                            "name": agent_name,
                            "prompt": prompt_content,
                            "prompt_file": os.path.join(prompts_dir, file)
                        }
                        
                        # Create agent with AiderAgent
                        self.agents[agent_name] = AiderAgent(agent_config)
                        self.web_instance.log_message(f"✓ Agent {agent_name} initialized", 'success')
                        
                    except Exception as e:
                        self.web_instance.log_message(f"Error initializing agent {agent_name}: {str(e)}", 'error')
                        continue

            if not self.agents:
                self.web_instance.log_message("No agents were initialized", 'warning')
                
        except Exception as e:
            self.web_instance.log_message(f"Error initializing agents: {str(e)}", 'error')
            raise

    def get_available_agents(self) -> List[str]:
        """Get list of available agent names"""
        return list(self.agents.keys())

    def start_all_agents(self) -> None:
        """Start all agents"""
        try:
            self.web_instance.log_message("🚀 Starting agents...", 'info')
            
            # Check available agents
            available_agents = self.get_available_agents()
            self.web_instance.log_message(f"Available agents: {available_agents}", 'debug')
            
            if not available_agents:
                self.web_instance.log_message("No agents available to start", 'warning')
                return
                
            # Get current mission from FileManager
            current_mission = self.web_instance.file_manager.current_mission
            if not current_mission:
                raise AgentError("No current mission set")

            # Initialize agents if not already done
            if not self.agents:
                self.web_instance.log_message("Initializing agents...", 'info')
                self.init_agents({
                    "anthropic_api_key": self.web_instance.config["anthropic_api_key"],
                    "openai_api_key": self.web_instance.config["openai_api_key"]
                })
                
                if not self.agents:
                    raise AgentError("Failed to initialize agents")

            # Get absolute path to project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            mission_dir = os.path.abspath(os.path.join(project_root, "missions", current_mission))
            
            self.web_instance.log_message(f"Using absolute mission path: {mission_dir}", 'debug')
                
            # Verify directory exists and is accessible
            if not os.path.exists(mission_dir):
                raise AgentError(f"Mission directory not found: {mission_dir}")
            if not os.access(mission_dir, os.R_OK | os.W_OK):
                raise AgentError(f"Insufficient permissions on: {mission_dir}")

            # Store thread references
            self.agent_threads = {}

            # Log agents to be started
            self.web_instance.log_message(f"Agents to start: {list(self.agents.keys())}", 'debug')

            # Update mission directory for all agents
            for name, agent in self.agents.items():
                agent.mission_dir = mission_dir
                self.web_instance.log_message(f"Set mission dir for {name}: {mission_dir}", 'debug')
                
            self.running = True
            
            # Start monitor thread
            self._start_monitor_thread()
            
            # Start each agent in a new thread
            for name, agent in self.agents.items():
                try:
                    self.web_instance.log_message(f"Starting agent {name}...", 'debug')
                    
                    # Initialize agent
                    agent.start()
                    self.web_instance.log_message(f"Agent {name} initialized", 'debug')
                    
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
                    self.web_instance.log_message(f"Started thread for {name}", 'debug')

                    # Verify thread started
                    if not thread.is_alive():
                        raise AgentError(f"Thread failed to start for agent {name}")
                        
                    self.web_instance.log_message(f"✓ Agent {name} thread confirmed running", 'success')
                    
                    # Add 6 second delay between agent starts
                    time.sleep(6)
                    
                except Exception as e:
                    self.web_instance.log_message(
                        f"Error starting agent {name}: {str(e)}\n{traceback.format_exc()}", 
                        'error'
                    )

            # Verify all threads are running
            running_threads = [name for name, thread in self.agent_threads.items() if thread.is_alive()]
            self.web_instance.log_message(f"Running agent threads: {running_threads}", 'debug')

            if len(running_threads) != len(self.agents):
                raise AgentError(f"Only {len(running_threads)} of {len(self.agents)} agents started")

            self.web_instance.log_message("✨ All agents active", 'success')
            
        except Exception as e:
            self.web_instance.log_message(
                f"Error starting agents: {str(e)}\n{traceback.format_exc()}", 
                'error'
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
                    self.web_instance.log_message(f"Agent {name} stopped", 'info')
                except Exception as e:
                    self.web_instance.log_message(f"Error stopping agent {name}: {str(e)}", 'error')
            
            # Stop monitor thread
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2)

            self.web_instance.log_message("All agents stopped", 'success')
            
        except Exception as e:
            self.web_instance.log_message(f"Error stopping agents: {str(e)}", 'error')
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
        """Wrapper function to catch any exceptions from agent run method"""
        try:
            self.web_instance.log_message(f"Agent {name} thread starting run method", 'debug')
            agent.run()
        except Exception as e:
            self.web_instance.log_message(
                f"Agent {name} thread crashed: {str(e)}\n{traceback.format_exc()}", 
                'error'
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

    def get_agent_prompt(self, agent_id: str) -> Optional[str]:
        """Get the current prompt for a specific agent"""
        try:
            agent_name = agent_id.lower()
            if agent_name not in self.agents:
                self.web_instance.log_message(f"Agent {agent_id} not found", 'error')
                return None
                
            agent = self.agents[agent_name]
            prompt = agent.get_prompt()
            
            # Log prompt access
            self.web_instance.log_message(f"Retrieved prompt for agent {agent_name}", 'debug')
            return prompt
            
        except Exception as e:
            self.web_instance.log_message(f"Error getting agent prompt: {str(e)}", 'error')
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
                self.web_instance.log_message(f"Saved new prompt for agent {agent_name}", 'success')
                
                # Stop agent if running
                if agent.running:
                    agent.stop()
                    self.web_instance.log_message(f"Stopped agent {agent_name} for prompt update", 'info')
                    
                    # Restart agent with new prompt
                    agent.start()
                    thread = threading.Thread(
                        target=self._run_agent_wrapper,
                        args=(agent_name, agent),
                        daemon=True,
                        name=f"Agent-{agent_name}"
                    )
                    thread.start()
                    self.web_instance.log_message(f"Restarted agent {agent_name} with new prompt", 'success')
                    
            return success
            
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
