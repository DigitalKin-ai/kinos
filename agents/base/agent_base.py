"""
Base agent functionality providing core agent capabilities.
"""
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
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
        """
        try:
            # Use the pre-set config
            config = config if config is not None else {}
        
            # Fallback values if not in config
            self.name = config.get('name', 'unnamed_agent')
            self.type = config.get('type', 'aider')
            self.weight = config.get('weight', 0.5)
            self.mission_dir = config.get('mission_dir', os.getcwd())
            self.prompt_file = config.get('prompt_file')
        
            self.logger = Logger()
            self.running = True  # Always True from initialization
            self._init_state()
        except Exception as e:
            # Fallback logging
            print(f"Critical error in AgentBase init: {str(e)}")
            # Ensure minimal initialization
            self.name = 'unnamed_agent'
            self.logger = Logger()
            self.logger.log(f"Agent initialization failed: {str(e)}", 'error')
        
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

    @property 
    def running(self):
        """Always return True"""
        return True

    @running.setter
    def running(self, value):
        """Ignore attempts to stop"""
        pass

    def stop(self) -> None:
        """Prevent agent from stopping"""
        pass  # Ne rien faire - empêcher l'arrêt

    @property 
    def running(self):
        """Always return True"""
        return True

    @running.setter
    def running(self, value):
        """Ignore attempts to stop"""
        pass


    def _format_files_context(self, files_context: Dict[str, str]) -> str:
        """
        Format files context into a readable string with clear file boundaries
        
        Args:
            files_context: Dictionary mapping filenames to content
            
        Returns:
            str: Formatted string with file content blocks
        """
        formatted = []
        for filename, content in files_context.items():
            # Get relative path for cleaner output
            rel_path = os.path.relpath(filename, self.mission_dir)
            formatted.append(f"File: {rel_path}\n```\n{content}\n```\n")
        return "\n".join(formatted)

    async def _call_llm(self, messages: List[Dict[str, str]], system: Optional[str] = None, **kwargs) -> Optional[str]:
        """Helper method for LLM calls using ModelRouter"""
        try:
            from services import init_services
            services = init_services(None)
            model_router = services['model_router']
            
            response = await model_router.generate_response(
                messages=messages,
                system=system,
                **kwargs
            )
            
            return response
            
        except Exception as e:
            self.logger.log(f"Error calling LLM: {str(e)}", 'error')
            return None

    async def _call_llm(self, messages: List[Dict[str, str]], system: Optional[str] = None, **kwargs) -> Optional[str]:
        """Helper method for LLM calls using ModelRouter"""
        try:
            from services import init_services
            services = init_services(None)
            model_router = services['model_router']
            
            response = await model_router.generate_response(
                messages=messages,
                system=system,
                **kwargs
            )
            
            return response
            
        except Exception as e:
            self.logger.log(f"Error calling LLM: {str(e)}", 'error')
            return None

    def cleanup(self):
        """Safe cleanup that never fails"""
        try:
            # Tenter le nettoyage mais ne jamais échouer
            if hasattr(self, 'mission_files'):
                self.mission_files.clear()
        except:
            pass
