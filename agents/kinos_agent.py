import os
import traceback
from typing import Optional
from utils.logger import Logger
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

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
            # Store original directory and configure encoding
            self.original_dir = os.getcwd()
            self._configure_encoding()
            
            # Initialize logger first for proper error reporting
            self.logger = self._init_logger(config.get("logger", print))
            
            # Validate required config fields
            required_fields = ['name', 'mission_dir']
            missing = [f for f in required_fields if f not in config]
            if missing:
                raise ValueError(f"Missing required config fields: {', '.join(missing)}")
            
            # Set core attributes
            self.name = config['name']
            self.config = config
            self.mission_dir = config['mission_dir']
            
            # Initialize state
            self.running = False
            self.last_run = None
            self.last_change = None
            self.consecutive_no_changes = 0
            self.error_count = 0
            self.mission_files = {}
            self._prompt_cache = {}
            
            # Load configuration and validate paths
            self._load_config()
            self._validate_paths()
            
            self.logger.log(f"[{self.__class__.__name__}] Initialized as {self.name}")
            
        except Exception as e:
            print(f"Error initializing agent: {str(e)}")  # Fallback logging
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

    def should_run(self) -> bool:
        """Determine if agent should execute based on time and phase"""
        try:
            # Get current phase first
            from services import init_services
            services = init_services(None)
            phase_service = services['phase_service']
            phase_status = phase_service.get_status_info()
            current_phase = phase_status['phase']

            # Get team configuration
            team_service = services['team_service']
            active_team = None
            for team in team_service.predefined_teams:
                if self.name in team.get('agents', []):
                    active_team = team
                    break

            if active_team and 'phase_config' in active_team:
                phase_config = active_team['phase_config'].get(current_phase.lower(), {})
                active_agents = phase_config.get('active_agents', [])
                
                # If agent list is specified and this agent is not in it, don't run
                if active_agents and self.name.lower() not in [a.lower() for a in active_agents]:
                    self.logger.log(
                        f"[{self.__class__.__name__}] ⏸️ Inactive in {current_phase} phase", 
                        'debug'
                    )
                    return False

            # Continue with existing time-based checks
            now = datetime.now()
            
            # First run
            if self.last_run is None:
                self._log(f"[{self.__class__.__name__}] 🔄 First run")
                return True
                
            # Calculate dynamic delay
            delay = self.calculate_dynamic_interval()
            
            # Check if enough time has elapsed
            time_since_last = (now - self.last_run).total_seconds()
            should_execute = time_since_last >= delay
            
            if should_execute:
                self._log(
                    f"[{self.__class__.__name__}] ✓ Should run "
                    f"(time since last: {time_since_last:.1f}s, phase: {current_phase})"
                )
            else:
                self._log(
                    f"[{self.__class__.__name__}] ⏳ Waiting "
                    f"({time_since_last:.1f}s/{delay}s, phase: {current_phase})", 
                    'debug'
                )
                
            return should_execute
            
        except Exception as e:
            self._log(f"[{self.__class__.__name__}] ❌ Error in should_run: {str(e)}")
            return False


    def calculate_dynamic_interval(self) -> float:
        """Enhanced dynamic interval calculation with bounds"""
        try:
            base_interval = self.check_interval
            min_interval = 60  # Minimum 1 minute
            max_interval = 3600  # Maximum 1 hour
            
            # Calculate multiplier based on activity
            if self.consecutive_no_changes > 0:
                # More aggressive backoff with upper bound
                multiplier = min(10, 1.5 ** min(5, self.consecutive_no_changes))
                
                # Apply error penalty if recent errors
                if hasattr(self, 'error_count') and self.error_count > 0:
                    multiplier *= 1.5
                    
                interval = base_interval * multiplier
                
                # Log adjustment
                self.logger.log(
                    f"[{self.__class__.__name__}] Adjusted interval: {interval:.1f}s "
                    f"(multiplier: {multiplier:.1f})", 
                    'debug'
                )
                
                # Ensure within bounds
                return max(min_interval, min(max_interval, interval))
                
            return max(min_interval, base_interval)
            
        except Exception as e:
            self.logger.log(f"[{self.__class__.__name__}] Error calculating interval: {str(e)}", 'error')
            return self.check_interval  # Return base interval on error

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
            self._log(f"[{self.name}] 🚀 Starting agent run loop")
            
            while self.running:
                try:
                    # Validate mission directory
                    if not os.path.exists(self.mission_dir):
                        self._log(f"[{self.name}] ❌ Mission directory not found")
                        time.sleep(60)
                        continue

                    # Update file list
                    self.list_files()
                    
                    # Get current prompt
                    prompt = self.get_prompt()
                    if not prompt:
                        self._log(f"[{self.name}] ⚠️ No prompt available")
                        time.sleep(60)
                        continue
                        
                    # Check if we should run
                    if not self.should_run():
                        interval = self.calculate_dynamic_interval()
                        time.sleep(interval)
                        continue
                        
                    # Run Aider with current prompt
                    result = self._run_aider(prompt)
                    
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

            self._log(f"[{self.name}] Run loop ended")
            
        except Exception as e:
            self._handle_error('run', e)
            self.running = False
            
        finally:
            # Ensure cleanup happens
            self.cleanup()
