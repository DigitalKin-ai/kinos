"""
Foundation for autonomous CLI-focused agents.

Each agent is responsible for:
- Dynamic file management and monitoring
- Independent decision making and execution
- Self-regulated operation cycles
- Automatic error recovery and adaptation

Key behaviors:
- Dynamic file management
- Flexible monitoring patterns
- Self-regulated execution
- Automatic error recovery
- Adaptive timing control
- Smart resource management
"""
import json
from typing import Dict, Any, Optional, List
import re
import time
import openai
import anthropic
import os
from datetime import datetime, timedelta
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
            self.original_dir = os.getcwd()
            
            # Configure UTF-8 encoding once
            self._configure_encoding()
            
            # Initialize core attributes first
            self._init_core_attributes(config)
            
            # Initialize logger (needed for all other operations)
            self.logger = self._init_logger(config.get("logger", print))
            
            # Validate and set paths
            self._validate_paths()
            
            # Initialize state tracking
            self._init_state()
            
            # Load configuration
            self._load_config()
            
            self.logger.log(f"[{self.__class__.__name__}] Initialized as {self.name}")
            
        except Exception as e:
            # Basic error logging even if logger isn't initialized
            print(f"Error initializing agent: {str(e)}")
            raise
        if callable(logger_config):
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

                    # If logger_config is a logging.Logger instance
                    if hasattr(logger_config, 'log'):
                        # Remove level from kwargs if present to avoid duplication
                        kwargs.pop('level', None)
                        return logger_config.log(msg, level)
                    
                    # If logger_config is a simple callable (like print)
                    return func(msg)

                return wrapper
                
            base_logger = create_log_wrapper(logger_config)
            
            # Create logger object with consistent interface but prevent __str__ output
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
                    
            self.logger = KinOSLogger()
        else:
            # Use logger object directly
            self.logger = logger_config

        # Now we can safely log since name is set
        self.logger.log(f"[{self.__class__.__name__}] Initialisé comme {self.name}")
        
        # Load intervals config
        self.intervals_config = self._load_intervals_config()
        
        # Get agent-specific interval or default
        self.check_interval = config.get(
            "check_interval",
            self._get_agent_interval()
        )
        
        self.running = False
        
    def _configure_encoding(self):
        """Configure UTF-8 encoding for CLI output"""
        import sys
        import codecs
        import locale
        
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
            
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')
            except locale.Error:
                pass

    def _init_core_attributes(self, config: Dict[str, Any]):
        """Initialize core attributes from config"""
        required_fields = ['name', 'mission_dir']
        missing = [f for f in required_fields if f not in config]
        if missing:
            raise ValueError(f"Missing required config fields: {', '.join(missing)}")
            
        self.name = config['name']
        self.config = config
        self.mission_dir = config['mission_dir']

    def _init_logger(self, logger_config) -> Any:
        """Initialize logger with consistent interface"""
        if callable(logger_config):
            return self._create_logger_wrapper(logger_config)
        return logger_config

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
        
        # Handle logger configuration
        logger_config = self.config.get("logger", print)
        if callable(logger_config):
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

                    # If logger_config is a logging.Logger instance
                    if hasattr(logger_config, 'log'):
                        # Remove level from kwargs if present to avoid duplication
                        kwargs.pop('level', None)
                        return logger_config.log(msg, level)
                    
                    # If logger_config is a simple callable (like print)
                    return func(msg)

                return wrapper
                
            base_logger = create_log_wrapper(logger_config)
            
            # Create logger object with consistent interface but prevent __str__ output
            class Logger:
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
                    
            self.logger = Logger()
        else:
            # Use logger object directly
            self.logger = logger_config
            
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
        self.running = False
        # Clean up any pending operations
        if hasattr(self, 'current_content'):
            self.write_file(self.current_content)
        
        # Restore original working directory
        try:
            os.chdir(self.original_dir)
        except Exception as e:
            self.logger.log(f"[{self.__class__.__name__}] Error restoring working directory: {str(e)}")
            
    def recover_from_error(self):
        """
        Tente de récupérer après une erreur.
        
        - Réinitialise l'état interne
        - Recharge les fichiers
        - Journalise la tentative
        
        Returns:
            bool: True si récupération réussie, False sinon
        """
        try:
            self.logger(f"[{self.__class__.__name__}] Attempting recovery...")
            
            # Reset internal state
            self.last_run = None
            self.last_change = None
            self.consecutive_no_changes = 0
            
            # Re-initialize file monitoring
            self.list_files()
            
            # Log recovery attempt
            self.logger(f"[{self.__class__.__name__}] Recovery complete")
            return True
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] Recovery failed: {str(e)}")
            return False

    def should_run(self) -> bool:
        """
        Détermine si l'agent doit s'exécuter.
        
        Returns:
            bool: True si l'agent doit s'exécuter
            
        Facteurs considérés:
        - Temps depuis dernière exécution
        - Niveau d'activité récent
        - Ajustements dynamiques du timing
        """
        now = datetime.now()
        
        # First run
        if self.last_run is None:
            return True
            
        # Calculate dynamic delay
        delay = self.calculate_dynamic_interval()
        
        # Check if enough time has elapsed
        return (now - self.last_run) >= timedelta(seconds=delay)


    def calculate_dynamic_interval(self) -> float:
        """
        Calcule l'intervalle optimal entre les exécutions.
        
        Returns:
            float: Intervalle calculé en secondes
            
        Facteurs pris en compte:
        - Fréquence récente des changements
        - Niveau d'activité système
        - Utilisation des ressources
        - Exigences temporelles spécifiques
        """
        base_interval = self.check_interval
        
        # If no recent changes, increase interval more aggressively
        if self.last_change and self.consecutive_no_changes > 0:
            # More aggressive backoff: up to 30x base rhythm
            multiplier = min(30, 2 ** min(4, self.consecutive_no_changes))
            return base_interval * multiplier
            
        # Add minimum delay to prevent rate limiting
        return max(base_interval, 80)  # At least 80 seconds between calls

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

    def run(self) -> None:
        """Main agent loop"""
        self.running = True
        self.logger(f"[{self.__class__.__name__}] Starting run loop")
        
        while self.running:
            try:
                if not self.should_run():
                    time.sleep(1)
                    continue

                # List files to watch
                self.list_files()
                
                # Log detailed debug info
                self.logger(f"[{self.__class__.__name__}] Starting execution cycle")
                self.logger(f"[{self.__class__.__name__}] Current prompt: {self.prompt[:100]}...")
                self.logger(f"[{self.__class__.__name__}] Watching files: {list(self.mission_files.keys())}")
                
                # Verify we have files to watch
                if not self.mission_files:
                    self.logger(f"[{self.__class__.__name__}] No files to watch, waiting...")
                    time.sleep(self.check_interval)
                    continue

                # Verify we have a valid prompt
                if not self.prompt or not self.prompt.strip():
                    self.logger(f"[{self.__class__.__name__}] No valid prompt, waiting...")
                    time.sleep(self.check_interval) 
                    continue

                # Execute Aider with agent's prompt
                if hasattr(self, '_run_aider'):
                    self.logger(f"[{self.__class__.__name__}] Calling _run_aider")
                    result = self._run_aider(self.prompt)
                    if result:
                        self.last_change = datetime.now()
                        self.consecutive_no_changes = 0
                        self.logger(f"[{self.__class__.__name__}] Changes made by Aider")
                    else:
                        self.consecutive_no_changes += 1
                        self.logger(f"[{self.__class__.__name__}] No changes made")
                else:
                    self.logger(f"[{self.__class__.__name__}] _run_aider method not implemented")
    
                # Update metrics
                self.last_run = datetime.now()
                
                # Adaptive pause
                interval = self.calculate_dynamic_interval()
                self.logger(f"[{self.__class__.__name__}] Sleeping for {interval} seconds")
                time.sleep(interval)
                
            except Exception as e:
                self.logger(f"[{self.__class__.__name__}] Error in agent loop: {str(e)}")
                time.sleep(5)  # Pause before retrying
                if not self.running:
                    break

        self.logger(f"[{self.__class__.__name__}] Run loop ended")
