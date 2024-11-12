"""PhaseService - Service for managing project phases based on token usage"""
import os
from enum import Enum
from typing import Dict, Any, Tuple
from datetime import datetime
from services.base_service import BaseService
from utils.logger import Logger

class ProjectPhase(Enum):
    EXPANSION = "EXPANSION"
    CONVERGENCE = "CONVERGENCE"

class PhaseService(BaseService):
    """Manages project phases based on token usage"""

    # System constants
    MODEL_TOKEN_LIMIT = 128_000
    CONVERGENCE_THRESHOLD = 0.60
    EXPANSION_THRESHOLD = 0.50
    
    # Derived values
    CONVERGENCE_TOKENS = int(MODEL_TOKEN_LIMIT * CONVERGENCE_THRESHOLD)
    EXPANSION_TOKENS = int(MODEL_TOKEN_LIMIT * EXPANSION_THRESHOLD)

    def __init__(self, _):  # Keep parameter for compatibility but don't use it
        self.logger = Logger()
        self.current_phase = ProjectPhase.EXPANSION
        self.last_transition = datetime.now()
        self.total_tokens = 0

    def determine_phase(self, total_tokens: int) -> Tuple[ProjectPhase, str]:
        """Determine appropriate phase based on token count"""
        self.total_tokens = total_tokens
        old_phase = self.current_phase
        
        if total_tokens > self.CONVERGENCE_TOKENS:
            self.current_phase = ProjectPhase.CONVERGENCE
            message = "Convergence needed - Token limit approaching"
        elif total_tokens < self.EXPANSION_TOKENS:
            self.current_phase = ProjectPhase.EXPANSION
            message = "Returning to expansion - Token usage optimized"
        else:
            message = "Maintaining current phase"
            
        # Log phase transition if it occurred
        if old_phase != self.current_phase:
            self.last_transition = datetime.now()
            self.logger.log(
                f"Phase transition: {old_phase.value} → {self.current_phase.value}\n"
                f"Reason: {message}",
                'info'
            )
            
        return self.current_phase, message

    def get_status_info(self) -> Dict[str, Any]:
        """Get current phase status information"""
        usage_percent = (self.total_tokens / self.MODEL_TOKEN_LIMIT) * 100
        
        # Determine status icon
        if usage_percent < 55:
            status_icon = "✓"
            status_message = "Below convergence threshold"
        elif usage_percent < 60:
            status_icon = "⚠️"
            status_message = "Approaching convergence threshold"
        else:
            status_icon = "🔴"
            status_message = "Convergence needed"
            
        # Calculate headroom
        if self.current_phase == ProjectPhase.EXPANSION:
            headroom = self.CONVERGENCE_TOKENS - self.total_tokens
        else:
            headroom = self.EXPANSION_TOKENS - self.total_tokens
            
        return {
            "phase": self.current_phase.value,
            "total_tokens": self.total_tokens,
            "usage_percent": usage_percent,
            "status_icon": status_icon,
            "status_message": status_message,
            "headroom": headroom,
            "last_transition": self.last_transition.isoformat()
        }

    def force_phase(self, phase: str) -> bool:
        """Force a specific phase (for debugging)"""
        try:
            new_phase = ProjectPhase(phase.upper())
            if new_phase != self.current_phase:
                self.current_phase = new_phase
                self.last_transition = datetime.now()
                self.logger.log(f"Phase manually set to: {new_phase.value}", 'warning')
            return True
        except ValueError:
            self.logger.log(f"Invalid phase: {phase}", 'error')
            return False
