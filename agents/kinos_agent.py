import os
import json
import traceback
import time
from typing import Optional, Dict, Any, Union
from datetime import datetime
from utils.logger import Logger
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from agents.aider.command_builder import AiderCommandBuilder
from agents.aider.output_parser import AiderOutputParser

class FileManager:
    """Service for managing file operations"""
    
    def __init__(self, web_instance, on_content_changed=None):
        """Initialize with minimal dependencies"""
        self.project_root = os.getcwd()
        self._on_content_changed = on_content_changed
        self.logger = Logger()
        self.content_cache = {}

    def read_file(self, file_name: str) -> Optional[str]:
        """Read file with simplified path handling"""
        try:
            file_path = os.path.join(os.getcwd(), file_name)
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.log(f"Error reading {file_name}: {str(e)}", 'error')
            return None
            
    def write_file(self, file_name: str, content: str) -> bool:
        """Write file with map update"""
        try:
            file_path = os.path.join(os.getcwd(), file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # Update map after any file change except map.md itself
            if file_name != 'map.md':
                # Get services and update map
                from services import init_services
                services = init_services(None)
                services['map_service'].update_map()
                
            return True
        except Exception as e:
            self.logger.log(f"Error writing {file_name}: {str(e)}", 'error')
            return False
            
    def reset_files(self) -> bool:
        """Reset all files to their initial state"""
        try:
            # Contenu initial par défaut
            initial_contents = {
                'demande': '# Mission Request\n\nDescribe the mission request here.',
                'specifications': '# Specifications\n\nDefine specifications here.',
                'evaluation': '# Evaluation\n\nEvaluation criteria and results.'
            }
            
            for file_name, content in initial_contents.items():
                if not self.write_file(file_name, content):
                    return False
            return True
        except Exception as e:
            self.logger.log(f"Error resetting files: {e}", 'error')
            return False
from typing import Dict, Any, Optional, List
import time
import os
from datetime import datetime
from functools import wraps
from enum import Enum, auto
from dataclasses import dataclass, field
import traceback
import random

class AgentStatus(Enum):
    """Enum representing different agent states"""
    INITIALIZING = auto()
    RUNNING = auto()
    IDLE = auto()
    ERROR = auto()
    RECOVERING = auto()

@dataclass
class PerformanceMetrics:
    """Comprehensive performance tracking"""
    execution_times: List[float] = field(default_factory=list)
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    avg_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = float('inf')
    
    def update(self, execution_time: float, success: bool):
        """Update metrics with new execution data"""
        self.total_runs += 1
        self.execution_times.append(execution_time)
        
        if success:
            self.successful_runs += 1
        else:
            self.failed_runs += 1
        
        # Keep only last 10 execution times
        self.execution_times = self.execution_times[-10:]
        
        # Recalculate metrics
        if self.execution_times:
            self.avg_response_time = sum(self.execution_times) / len(self.execution_times)
            self.max_response_time = max(self.execution_times)
            self.min_response_time = min(self.execution_times)

class KinOSAgent:
    """
    Foundation for autonomous file-focused agents.
    
    Each agent is responsible for:
    - Monitoring and updating its dedicated file
    - Analyzing changes in related files
    - Making independent decisions
    - Adapting its execution rhythm
    
    Key behaviors:
    - File-based state persistence
    - Self-regulated execution cycles
    - Automatic error recovery
    - Activity-based timing adjustments
    """
    

    def __init__(self, config: Dict[str, Any]):
        """Initialize agent with configuration"""
        try:
            # Store original directory
            self.original_dir = os.getcwd()
            
            # Get services
            from services import init_services
            services = init_services(None)
            team_service = services['team_service']
            
            # Get active team info without modifying it
            active_team = team_service.get_active_team()
            if not active_team:
                raise ValueError("No active team set")
                
            # Set team info from active team
            self.team = active_team.get('name', 'default')
            self.team_name = active_team.get('display_name', self.team.title())
            
            # Update config with team info
            config['team'] = self.team
            
            # Initialize parent
            super().__init__(config)
            
            # Configure components
            self._configure_encoding()
            self.command_builder = AiderCommandBuilder(self.name)
            self.output_parser = AiderOutputParser(self.logger, self.name)
            
            self.logger.log(f"[{self.name}] Initialized in team {self.team_name}")
            
        except Exception as e:
            logger = Logger()
            logger.log(f"[INIT] Error during initialization: {str(e)}", 'error')
            raise
        

    def _init_core_attributes(self, config: Dict[str, Any]):
        """Initialize core attributes from config"""
        required_fields = ['name', 'mission_dir']
        missing = [f for f in required_fields if f not in config]
        if missing:
            raise ValueError(f"Missing required config fields: {', '.join(missing)}")
            
        self.name = config['name']
        self.config = config
        self.mission_dir = config['mission_dir']

    def _init_logger(self, logger_func) -> Any:
        """Initialize logger with consistent interface"""
        if callable(logger_func):
            # Create wrapper that handles both Logger instances and simple callables
            def create_log_wrapper(func):
                def wrapper(*args, **kwargs):
                    # Extract message and level
                    if len(args) >= 2:
                        message, level = args[0], args[1]
                    else:
                        message = args[0] if args else kwargs.get('message', '')
                        level = kwargs.get('level', 'info')

                    # Convert message to string
                    msg = str(message)

                    # If logger_func has log method
                    if hasattr(logger_func, 'log'):
                        # Remove level from kwargs if present to avoid duplication
                        kwargs.pop('level', None)
                        return logger_func.log(msg, level)
                    
                    # If logger_func is a simple callable (like print)
                    return func(msg)

                return wrapper
                
            base_logger = create_log_wrapper(logger_func)
            
            # Create logger object with consistent interface
            class KinOSLogger:
                def log(self, *args, **kwargs):
                    return base_logger(*args, **kwargs)
                def _log(self, *args, **kwargs):
                    return base_logger(*args, **kwargs)
                def __call__(self, *args, **kwargs):
                    return base_logger(*args, **kwargs)
                def __str__(self):
                    return "KinOSLogger"
                def __repr__(self):
                    return "KinOSLogger"
                    
            return KinOSLogger()
        return logger_func

    def _init_state(self):
        """Initialize agent state tracking"""
        self.running = False
        self.last_run = None
        self.last_change = None
        self.consecutive_no_changes = 0
        self.error_count = 0
        self.mission_files = {}
        self._prompt_cache = {}

    def _load_config(self):
        """Load agent configuration"""
        self.intervals_config = self._load_intervals_config()
        self.check_interval = self.config.get(
            "check_interval",
            self._get_agent_interval()
        )

    def _validate_paths(self):
        """Validate all required paths"""
        if not os.path.exists(self.mission_dir):
            raise ValueError(f"Mission directory not found: {self.mission_dir}")
        if not os.access(self.mission_dir, os.R_OK | os.W_OK):
            raise ValueError(f"Insufficient permissions on mission directory: {self.mission_dir}")

    def _load_intervals_config(self) -> Dict:
        """Load agent intervals from config file"""
        try:
            config_path = os.path.join("config", "agent_intervals.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            return {"default": 60, "intervals": {}}
        except Exception as e:
            self.logger.log(f"Error loading intervals config: {str(e)}", 'error')
            return {"default": 60, "intervals": {}}

    def _get_agent_interval(self) -> int:
        """Get interval for this agent type"""
        agent_type = self.__class__.__name__.lower().replace('agent', '')
        return self.intervals_config["intervals"].get(
            agent_type,
            self.intervals_config["default"]
        )
        
        self.last_run = None
        self.last_change = None
        self.consecutive_no_changes = 0


    def start(self) -> None:
        """
        Démarre l'agent.
        
        - Active le flag running
        - Réinitialise les métriques
        - Prépare l'agent pour l'exécution
        """
        self.running = True
        # Reset metrics
        self.last_run = None
        self.last_change = None
        self.consecutive_no_changes = 0
        
        # Change to mission directory if this is a ValidationAgent
        if self.__class__.__name__ == 'ValidationAgent':
            if not os.path.exists(self.mission_dir):
                raise ValueError(f"Mission directory not found: {self.mission_dir}")
            os.chdir(self.mission_dir)


    def stop(self) -> None:
        """
        Arrête l'agent proprement.
        
        - Désactive le flag running
        - Termine les opérations en cours
        - Sauvegarde l'état final
        """
        try:
            with self._log_lock:
                self.logger.log(f"[{self.__class__.__name__}] Stopping agent")
            
            self.running = False
            # Clean up any pending operations
            if hasattr(self, 'current_content'):
                self.write_file(self.current_content)
            
            # Restore original working directory
            try:
                os.chdir(self.original_dir)
            except Exception as e:
                with self._log_lock:
                    self.logger.log(f"[{self.__class__.__name__}] Error restoring working directory: {str(e)}")
        except Exception as e:
            print(f"Error stopping agent: {str(e)}")  # Fallback to print

    def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities based on type"""
        try:
            capabilities = {
                'aider': {
                    'can_modify_files': True,
                    'can_execute_commands': False,
                    'can_research': False,
                    'priority_level': 1
                },
                'research': {
                    'can_modify_files': True,
                    'can_execute_commands': False,
                    'can_research': True,
                    'priority_level': 2
                }
            }
            
            return capabilities.get(self.type, capabilities['aider'])
            
        except Exception as e:
            self.logger.log(f"Error getting capabilities: {str(e)}", 'error')
            return capabilities['aider']

    def validate_operation(self, operation_type: str) -> bool:
        """Validate if agent can perform operation based on type"""
        try:
            capabilities = self.get_agent_capabilities()
            
            operation_requirements = {
                'file_modification': 'can_modify_files',
                'command_execution': 'can_execute_commands',
                'research': 'can_research'
            }
            
            required_capability = operation_requirements.get(operation_type)
            if not required_capability:
                return False
                
            return capabilities.get(required_capability, False)
            
        except Exception as e:
            self.logger.log(f"Error validating operation: {str(e)}", 'error')
            return False


    def validate_prompt(self, content: str) -> bool:
        """Validate prompt content format"""
        try:
            if not content or not content.strip():
                return False
                
            # Check minimum size
            if len(content) < 10:
                return False
                
            # Check required sections
            required = ["MISSION:", "CONTEXT:", "INSTRUCTIONS:", "RULES:"]
            for section in required:
                if section not in content:
                    self.logger.log(f"Missing required section: {section}", 'warning')
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.log(f"Error validating prompt: {str(e)}", 'error')
            return False

    def cleanup(self):
        """Cleanup agent resources properly"""
        try:
            # Stop agent if running
            if self.running:
                self.stop()
                
            # Clear caches
            if hasattr(self, '_prompt_cache'):
                self._prompt_cache.clear()
                
            # Restore original directory
            if hasattr(self, 'original_dir') and self.original_dir:
                try:
                    os.chdir(self.original_dir)
                except Exception as e:
                    self.logger.log(f"Error restoring directory: {str(e)}", 'error')
                    
            # Clear file tracking
            if hasattr(self, 'mission_files'):
                self.mission_files.clear()
                
            # Flush logger if possible
            if hasattr(self, 'logger'):
                try:
                    if hasattr(self.logger, 'flush'):
                        self.logger.flush()
                except:
                    pass
                    
        except Exception as e:
            # Use print as logger may be unavailable
            print(f"Error in cleanup: {str(e)}")

    def execute_mission(self, prompt: str) -> Optional[str]:
        """
        Enhanced mission execution with comprehensive tracking and error management
        """
        start_time = time.time()
        attempt = 0
        max_attempts = 3

        while attempt < max_attempts:
            try:
                # Performance tracking
                attempt_start = time.time()

                # Validate run conditions
                if not self._validate_run_conditions(prompt):
                    self.logger.log(
                        f"[{self.name}] Run conditions not met (Attempt {attempt+1})", 
                        'warning'
                    )
                    return None

                # Execute mission
                result = self._specific_mission_execution(prompt)

                # Performance metrics
                execution_time = time.time() - attempt_start
                self._update_performance_metrics(execution_time)

                # State management
                if result:
                    self.last_change = datetime.now()
                    self.consecutive_no_changes = 0
                    self.logger.log(
                        f"[{self.name}] Mission successful (Time: {execution_time:.2f}s)", 
                        'success'
                    )
                else:
                    self.consecutive_no_changes += 1
                    self.logger.log(
                        f"[{self.name}] No changes detected (Attempt {attempt+1})", 
                        'warning'
                    )

                return result

            except Exception as e:
                self._handle_error('execute_mission', e, {
                    'prompt': prompt,
                    'attempt': attempt + 1
                })
                attempt += 1
                
                # Adaptive backoff
                backoff_time = min(30, 2 ** attempt)
                time.sleep(backoff_time)

        # Final failure logging
        self.logger.log(
            f"[{self.name}] Mission failed after {max_attempts} attempts", 
            'critical'
        )
        return None

    def _specific_mission_execution(self, prompt: str) -> Optional[str]:
        """
        Placeholder for agent-specific mission execution logic
        
        Subclasses like AiderAgent will override this method
        """
        raise NotImplementedError("Subclasses must implement mission execution")

    def _update_performance_metrics(self, execution_time: float) -> None:
        """
        Update agent performance metrics
        
        Args:
            execution_time: Time taken for mission execution
        """
        try:
            # Initialize metrics if not exist
            if not hasattr(self, '_execution_times'):
                self._execution_times = []
            
            # Store execution time
            self._execution_times.append(execution_time)
            
            # Keep only last 10 execution times
            self._execution_times = self._execution_times[-10:]
            
            # Calculate metrics
            self.avg_response_time = sum(self._execution_times) / len(self._execution_times)
            self.min_response_time = min(self._execution_times)
            self.max_response_time = max(self._execution_times)
            
            # Log performance if it exceeds threshold
            if execution_time > (self.avg_response_time * 2):
                self.logger.log(
                    f"[{self.name}] Slow execution detected: {execution_time:.2f}s "
                    f"(Avg: {self.avg_response_time:.2f}s)", 
                    'warning'
                )
        except Exception as e:
            self.logger.log(f"Error updating performance metrics: {str(e)}", 'error')

    def _validate_run_conditions(self, prompt: str) -> bool:
        """
        Validate conditions required for mission execution
        
        Args:
            prompt: Mission prompt to validate
            
        Returns:
            bool: Whether conditions are met for execution
        """
        try:
            # Check mission directory
            if not os.path.exists(self.mission_dir):
                self.logger.log(f"[{self.name}] Mission directory not found", 'error')
                return False
            
            # Verify file access
            if not os.access(self.mission_dir, os.R_OK | os.W_OK):
                self.logger.log(f"[{self.name}] Insufficient permissions", 'error')
                return False
            
            # Check for monitored files
            if not self.mission_files:
                self.logger.log(f"[{self.name}] No files to monitor", 'warning')
                return False
            
            # Validate prompt
            if not prompt or not prompt.strip():
                self.logger.log(f"[{self.name}] Empty or invalid prompt", 'error')
                return False
            
            return True
            
        except Exception as e:
            self.logger.log(f"[{self.name}] Error validating run conditions: {str(e)}", 'error')
            return False
            
    def recover_from_error(self) -> bool:
        """Enhanced error recovery with state preservation"""
        try:
            self.logger.log(f"[{self.__class__.__name__}] Starting recovery...")
            
            # Store current state
            previous_state = {
                'running': self.running,
                'last_run': self.last_run,
                'last_change': self.last_change,
                'mission_files': dict(self.mission_files)
            }
            
            try:
                # Reset state
                self._init_state()
                
                # Re-validate paths
                self._validate_paths()
                
                # Reload files
                self.list_files()
                
                # Verify recovery
                if not self.mission_files:
                    raise ValueError("Failed to reload mission files")
                    
                self.logger.log(f"[{self.__class__.__name__}] Recovery successful")
                return True
                
            except Exception as recovery_error:
                # Restore previous state on failed recovery
                self.running = previous_state['running']
                self.last_run = previous_state['last_run']
                self.last_change = previous_state['last_change']
                self.mission_files = previous_state['mission_files']
                
                raise recovery_error
                
        except Exception as e:
            self.logger.log(f"[{self.__class__.__name__}] Recovery failed: {str(e)}", 'error')
            return False

    def _store_error_log(self, error_details: Dict[str, Any]) -> None:
        """
        Store error details in a rolling log file
        
        Args:
            error_details: Dictionary of error information
        """
        try:
            # Ensure error log directory exists
            error_log_dir = os.path.join(self.mission_dir, 'error_logs')
            os.makedirs(error_log_dir, exist_ok=True)
            
            # Generate log filename
            log_filename = f"errors_{datetime.now().strftime('%Y%m%d')}.jsonl"
            log_path = os.path.join(error_log_dir, log_filename)
            
            # Append error as JSON line
            with open(log_path, 'a', encoding='utf-8') as f:
                json.dump(error_details, f)
                f.write('\n')
                
        except Exception as e:
            print(f"Error storing error log: {str(e)}")

    def should_run(self) -> bool:
        """Determine if agent should execute based on time"""
        try:
            now = datetime.now()
        
            # First run
            if self.last_run is None:
                self.logger.log(f"[{self.__class__.__name__}] 🔄 First run")
                return True
            
            # Calculate dynamic delay
            delay = self.calculate_dynamic_interval()
        
            # Check if enough time has elapsed
            time_since_last = (now - self.last_run).total_seconds()
            should_execute = time_since_last >= delay
        
            if should_execute:
                self.logger.log(
                    f"[{self.__class__.__name__}] ✓ Should run "
                    f"(time since last: {time_since_last:.1f}s)"
                )
            else:
                self.logger.log(
                    f"[{self.__class__.__name__}] ⏳ Waiting "
                    f"({time_since_last:.1f}s/{delay}s)", 
                    'debug'
                )
            
            return should_execute
        
        except Exception as e:
            self.logger.log(f"[{self.__class__.__name__}] ❌ Error in should_run: {str(e)}")
            return False


    def calculate_dynamic_interval(self) -> float:
        """Calculate dynamic interval based on weight and activity"""
        try:
            base_interval = self.check_interval
            min_interval = 60  # Minimum 1 minute
            max_interval = 3600  # Maximum 1 hour
            
            # Get effective weight
            weight = self.get_effective_weight()
            
            # Calculate multiplier based on activity and weight
            if self.consecutive_no_changes > 0:
                multiplier = min(10, 1.5 ** min(5, self.consecutive_no_changes))
                
                # Apply error penalty if recent errors
                if self.error_count > 0:
                    multiplier *= 1.5
                    
                # Apply weight - higher weight means shorter interval
                weight_factor = 2 - weight  # Convert 0-1 weight to 1-2 range
                multiplier *= weight_factor
                
                interval = base_interval * multiplier
                
                # Log adjustment with weight info
                self.logger.log(
                    f"[{self.__class__.__name__}] Adjusted interval: {interval:.1f}s "
                    f"(multiplier: {multiplier:.1f}, weight: {weight:.1f})", 
                    'debug'
                )
                
                return max(min_interval, min(max_interval, interval))
                
            # Apply weight to base interval
            weight_factor = 2 - weight
            interval = base_interval * weight_factor
            return max(min_interval, min(max_interval, interval))
            
        except Exception as e:
            self.logger.log(f"[{self.__class__.__name__}] Error calculating interval: {str(e)}", 'error')
            return self.check_interval

    def is_healthy(self) -> bool:
        """
        Vérifie l'état de santé de l'agent.
        
        Returns:
            bool: True si l'agent est en bon état, False sinon
            
        Vérifie:
        - Dernier run < 2x check_interval 
        - Pas trop d'erreurs consécutives
        - Fichiers accessibles
        """

    def get_health_metrics(self) -> Dict[str, Any]:
        """Get comprehensive health metrics"""
        try:
            return {
                'status': {
                    'running': self.running,
                    'is_healthy': self.is_healthy(),
                    'last_run': self.last_run.isoformat() if self.last_run else None,
                    'last_change': self.last_change.isoformat() if self.last_change else None
                },
                'performance': {
                    'consecutive_no_changes': self.consecutive_no_changes,
                    'current_interval': self.calculate_dynamic_interval(),
                    'error_count': getattr(self, 'error_count', 0)
                },
                'resources': {
                    'mission_files': len(self.mission_files),
                    'cache_size': len(self._prompt_cache),
                    'working_dir': os.getcwd()
                }
            }
        except Exception as e:
            self.logger.log(f"[{self.__class__.__name__}] Error getting health metrics: {str(e)}", 'error')
            return {
                'error': str(e),
                'status': {'running': False, 'is_healthy': False}
            }
        try:
            # Vérifier le dernier run
            if self.last_run:
                time_since_last_run = (datetime.now() - self.last_run).total_seconds()
                if time_since_last_run > (self.check_interval * 2):
                    self.logger(f"[{self.__class__.__name__}] Inactif depuis {time_since_last_run}s", 'warning')
                    return False
                
            # Vérifier le nombre d'erreurs consécutives
            if hasattr(self, 'consecutive_no_changes') and self.consecutive_no_changes > 5:
                self.logger(f"[{self.__class__.__name__}] Trop d'exécutions sans changement: {self.consecutive_no_changes}", 'warning')
                return False
                
            return True
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] Erreur vérification santé: {str(e)}", 'error')
            return False

    def get_effective_weight(self) -> float:
        """Get effective weight"""
        try:
            return self.weight
        
        except Exception as e:
            self.logger.log(f"Error getting effective weight: {str(e)}", 'error')
            return self.weight

    def _validate_run_conditions(self) -> bool:
        """Validate conditions required for running"""
        try:
            # Check mission directory
            if not os.path.exists(self.mission_dir):
                self.logger.log(f"[{self.__class__.__name__}] Mission directory not found", 'error')
                return False
                
            # Verify file access
            if not os.access(self.mission_dir, os.R_OK | os.W_OK):
                self.logger.log(f"[{self.__class__.__name__}] Insufficient permissions", 'error')
                return False
                
            # Check for monitored files
            if not self.mission_files:
                self.logger.log(f"[{self.__class__.__name__}] No files to monitor", 'warning')
                return False
                
            # Verify prompt
            if not hasattr(self, 'prompt') or not self.prompt or not self.prompt.strip():
                self.logger.log(f"[{self.__class__.__name__}] No valid prompt", 'error')
                return False
                
            return True
            
        except Exception as e:
            self.logger.log(f"[{self.__class__.__name__}] Error validating run conditions: {str(e)}", 'error')
            return False

    def run(self):
        """Main execution loop for the agent"""
        try:
            self.logger.log(f"[{self.name}] 🚀 Starting agent run loop")
        
            while self.running:
                try:
                    # Validate mission directory
                    if not os.path.exists(self.mission_dir):
                        self.logger.log(f"[{self.name}] ❌ Mission directory not found")
                        time.sleep(60)
                        continue

                    # Update file list
                    self.list_files()
                
                    # Get current prompt
                    prompt = self.get_prompt()
                    if not prompt:
                        self.logger.log(f"[{self.name}] ⚠️ No prompt available")
                        time.sleep(60)
                        continue
                    
                    # Execute mission
                    result = self.execute_mission(prompt)
                
                    # Update state based on result
                    self.last_run = datetime.now()
                    if result:
                        self.last_change = datetime.now()
                        self.consecutive_no_changes = 0
                    else:
                        self.consecutive_no_changes += 1
                    
                except Exception as loop_error:
                    self._handle_error('run_loop', loop_error)
                    time.sleep(5)  # Brief pause before retrying

            self.logger.log(f"[{self.name}] Run loop ended")
        
        except Exception as e:
            # Ignore known benign Aider errors
            if any(err in str(e) for err in [
                "Can't initialize prompt toolkit",
                "No Windows console found",
                "aider.chat/docs/troubleshooting/edit-errors.html",
                "[Errno 22] Invalid argument"
            ]):
                pass  # Do not stop the agent
            else:
                self.logger.log(f"[{self.name}] Critical error in run: {str(e)}", 'error')
                self.running = False
        
        finally:
            # Ensure cleanup happens
            self.cleanup()
