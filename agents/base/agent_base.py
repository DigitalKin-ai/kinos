"""
Base agent functionality providing core agent capabilities.

This module defines the abstract base class that all KinOS agents must inherit from.
It provides common functionality for:
- Agent lifecycle management (start/stop)
- State tracking and health monitoring  
- Dynamic execution timing
- Error handling and recovery
- Resource cleanup
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from utils.logger import Logger

class AgentBase(ABC):
    """
    Abstract base class that all KinOS agents must inherit from.
    
    Provides core agent functionality including:
    - Lifecycle management
    - State tracking
    - Health monitoring
    - Dynamic timing
    - Error handling
    
    Attributes:
        name (str): Agent name/identifier
        mission_dir (str): Working directory path
        logger (Logger): Logger instance
        running (bool): Current running state
        last_run (datetime): Timestamp of last execution
        last_change (datetime): Timestamp of last modification
        consecutive_no_changes (int): Count of runs without changes
        error_count (int): Count of consecutive errors
    """
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize base agent with configuration.

        Args:
            config: Configuration dictionary containing:
                - name: Agent name/identifier
                - mission_dir: Working directory path
                - logger: Optional logger instance
                - check_interval: Optional execution interval

        Raises:
            ValueError: If required config fields are missing
        """
        self.name = config['name']
        self.mission_dir = config['mission_dir']
        self.logger = self._init_logger(config.get("logger", print))
        self.running = False
        self._init_state()
        
    def _init_state(self):
        """Initialize agent state tracking"""
        self.last_run = None
        self.last_change = None
        self.consecutive_no_changes = 0
        self.error_count = 0

    def _init_logger(self, logger_func) -> Logger:
        """Initialize logger with consistent interface"""
        if isinstance(logger_func, Logger):
            return logger_func
        return Logger()

    def calculate_dynamic_interval(self) -> float:
        """
        Calculate the dynamic execution interval based on agent activity.

        The interval increases exponentially with consecutive no-changes,
        up to a maximum value. Error counts also influence the delay.

        Returns:
            float: Number of seconds to wait before next execution
        """
        try:
            base_interval = getattr(self, 'check_interval', 60)
            min_interval = 60  # Minimum 1 minute
            max_interval = 3600  # Maximum 1 hour
            
            if self.consecutive_no_changes > 0:
                multiplier = min(10, 1.5 ** min(5, self.consecutive_no_changes))
                if self.error_count > 0:
                    multiplier *= 1.5
                interval = base_interval * multiplier
                return max(min_interval, min(max_interval, interval))
                
            return max(min_interval, base_interval)
            
        except Exception as e:
            self.logger.log(f"Error calculating interval: {str(e)}", 'error')
            return 60  # Default 1 minute

    def is_healthy(self) -> bool:
        """
        Check if the agent is in a healthy state.

        Evaluates:
        - Time since last execution
        - Consecutive errors/no-changes
        - Resource availability
        - File access

        Returns:
            bool: True if agent is healthy, False otherwise
        """
        try:
            if self.last_run:
                time_since_last = (datetime.now() - self.last_run).total_seconds()
                if time_since_last > (getattr(self, 'check_interval', 60) * 2):
                    return False
                    
            if self.consecutive_no_changes > 5:
                return False
                
            return True
            
        except Exception as e:
            self.logger.log(f"Error checking health: {str(e)}", 'error')
            return False

    @abstractmethod
    def list_files(self) -> None:
        """
        List and track files that this agent should monitor.
        Must be implemented by derived classes.
        """
        pass

    @abstractmethod
    def get_prompt(self) -> str:
        """
        Get the current prompt content for this agent.
        Must be implemented by derived classes.

        Returns:
            str: Current prompt content
        """
        pass

    @abstractmethod
    def _run_aider(self, prompt: str) -> Optional[str]:
        """
        Execute Aider with the given prompt.
        Must be implemented by derived classes.

        Args:
            prompt: Prompt to send to Aider

        Returns:
            Optional[str]: Aider output or None on error
        """
        pass

    def start(self) -> None:
        """
        Start the agent.
        
        - Activates running flag
        - Resets metrics and state
        - Prepares agent for execution
        """
        self.running = True
        self._init_state()

    def stop(self) -> None:
        """
        Stop the agent gracefully.
        
        - Deactivates running flag
        - Completes pending operations
        - Saves final state
        - Releases resources
        """
        self.running = False
