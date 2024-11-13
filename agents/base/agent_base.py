"""
Base agent functionality providing core agent capabilities.
"""
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
from utils.logger import Logger
from agents.base.file_handler import FileHandler

class AgentBase(ABC):
    """
    Abstract base class that all KinOS agents must inherit from.
    
    Provides core agent functionality including:
    - Lifecycle management
    - State tracking
    - Health monitoring
    - Dynamic timing
    - Error handling
    """
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize base agent with configuration.

        Args:
            config: Configuration dictionary containing:
                - name: Agent name/identifier
                - mission_dir: Working directory path
                - prompt_file: Path to prompt file
        """
        self.name = config['name']
        self.mission_dir = config['mission_dir']
        self.prompt_file = config.get('prompt_file')
        self.logger = Logger()
        self.running = False
        self._init_state()
        
    def _init_state(self):
        """Initialize agent state tracking"""
        self.last_run = None
        self.last_change = None
        self.consecutive_no_changes = 0
        self.error_count = 0
        self.mission_files = {}

    def calculate_dynamic_interval(self) -> float:
        """
        Calculate the dynamic execution interval based on agent activity.

        Returns:
            float: Number of seconds to wait before next execution
        """
        try:
            base_interval = 60  # Default 1 minute
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
            return 60

    def is_healthy(self) -> bool:
        """
        Check if the agent is in a healthy state.

        Returns:
            bool: True if agent is healthy
        """
        try:
            if self.last_run:
                time_since_last = (datetime.now() - self.last_run).total_seconds()
                if time_since_last > 120:  # 2 minutes
                    return False
                    
            if self.consecutive_no_changes > 5:
                return False
                
            return True
            
        except Exception as e:
            self.logger.log(f"Error checking health: {str(e)}", 'error')
            return False

    def list_files(self) -> None:
        """List and track files that this agent should monitor"""
        try:
            # Use FileHandler to list files in mission directory
            file_handler = FileHandler(self.mission_dir, self.logger)
            self.mission_files = file_handler.list_files()
            
            # Log files being monitored
            if self.mission_files:
                self.logger.log(
                    f"[{self.name}] Monitoring {len(self.mission_files)} files:\n" + 
                    "\n".join(f"  - {os.path.relpath(f, self.mission_dir)}" for f in self.mission_files.keys()), 
                    'info'
                )
            else:
                self.logger.log(
                    f"[{self.name}] No files found to monitor in {self.mission_dir}", 
                    'warning'
                )
                
        except Exception as e:
            self.logger.log(
                f"[{self.name}] Error listing files: {str(e)}", 
                'error'
            )

    @abstractmethod
    def get_prompt(self) -> str:
        """Get the current prompt content"""
        pass

    @abstractmethod
    def _run_aider(self, prompt: str) -> Optional[str]:
        """Execute Aider with the given prompt"""
        pass

    def start(self) -> None:
        """Start the agent"""
        self.running = True
        self._init_state()
        self.logger.log(f"[{self.name}] Agent started", 'info')

    def stop(self) -> None:
        """Stop the agent gracefully"""
        self.running = False
        self.cleanup()

    def cleanup(self):
        """Clean up agent resources"""
        try:
            self.running = False
            self.mission_files.clear()
        except Exception as e:
            self.logger.log(f"Error in cleanup: {str(e)}", 'error')
