"""Base agent functionality"""
from datetime import datetime
from typing import Dict, Any, Optional
from utils.logger import Logger

class AgentBase:
    """Base class with core agent functionality"""
    def __init__(self, config: Dict[str, Any]):
        """Initialize base agent with configuration"""
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
        """Calculate dynamic execution interval"""
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
        """Check agent health status"""
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

    def start(self) -> None:
        """Start the agent"""
        self.running = True
        self._init_state()

    def stop(self) -> None:
        """Stop the agent"""
        self.running = False
