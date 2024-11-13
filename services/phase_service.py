"""PhaseService - Service for managing project phases based on token usage"""
from enum import Enum
from typing import Dict, Any, Tuple
from datetime import datetime
from services.base_service import BaseService
from utils.logger import Logger
from utils.constants import (
    MODEL_TOKEN_LIMIT,
    CONVERGENCE_THRESHOLD,
    EXPANSION_THRESHOLD
)

class ProjectPhase(Enum):
    EXPANSION = "EXPANSION"
    CONVERGENCE = "CONVERGENCE"

class PhaseService(BaseService):
    """Manages project phases based on token usage"""
    
    # Class constants
    MODEL_TOKEN_LIMIT = 128_000
    CONVERGENCE_THRESHOLD = 0.60
    EXPANSION_THRESHOLD = 0.50
    CONVERGENCE_TOKENS = int(MODEL_TOKEN_LIMIT * CONVERGENCE_THRESHOLD)
    EXPANSION_TOKENS = int(MODEL_TOKEN_LIMIT * EXPANSION_THRESHOLD)

    # Class-level state storage
    _state = {
        'current_phase': ProjectPhase.EXPANSION,
        'total_tokens': 0,
        'last_transition': datetime.now()
    }

    @classmethod
    def get_state(cls):
        """Get current state, initializing if needed"""
        return cls._state

    def __init__(self, _):  # Keep parameter for compatibility but don't use it
        """Initialize with logger only"""
        self.logger = Logger()

    def determine_phase(self, total_tokens: int) -> Tuple[ProjectPhase, str]:
        """Determine appropriate phase based on token count"""
        try:
            print(f"[DEBUG] determine_phase() called with {total_tokens} tokens")
            state = self.get_state()
            print(f"[DEBUG] Current phase before update: {state['current_phase'].value}")
            print(f"[DEBUG] Current total_tokens before update: {state['total_tokens']}")
            
            # Store total tokens first
            state['total_tokens'] = max(0, total_tokens)  # Ensure non-negative
            old_phase = state['current_phase']
            
            # Calculate usage percentage
            usage_percent = (state['total_tokens'] / self.MODEL_TOKEN_LIMIT) * 100
            print(f"[DEBUG] Usage percent: {usage_percent:.1f}%")
            
            # Determine phase based on thresholds
            if usage_percent >= self.CONVERGENCE_THRESHOLD * 100:
                new_phase = ProjectPhase.CONVERGENCE
                message = f"Convergence needed - Token usage at {usage_percent:.1f}%"
                print(f"[DEBUG] Threshold exceeded, switching to CONVERGENCE")
            else:
                new_phase = ProjectPhase.EXPANSION
                message = f"Expansion phase - Token usage at {usage_percent:.1f}%"
                print(f"[DEBUG] Below threshold, switching to EXPANSION")
            
            # Log phase transition ONLY if phase actually changed
            if new_phase != old_phase:
                print(f"[DEBUG] Phase changing from {old_phase.value} to {new_phase.value}")
                state['current_phase'] = new_phase
                state['last_transition'] = datetime.now()
                self.logger.log(
                    f"Phase transition: {old_phase.value} → {new_phase.value}\n"
                    f"Reason: {message}\n"
                    f"Total tokens: {state['total_tokens']:,}\n"
                    f"Usage: {usage_percent:.1f}%",
                    'info'
                )
            else:
                print(f"[DEBUG] Phase unchanged: {new_phase.value}")
                state['current_phase'] = new_phase
                
            print(f"[DEBUG] Final phase: {state['current_phase'].value}")
            print(f"[DEBUG] Final total_tokens: {state['total_tokens']}")
            
            return new_phase, message

        except Exception as e:
            print(f"[ERROR] Error in determine_phase: {str(e)}")
            self.logger.log(f"Error determining phase: {str(e)}", 'error')
            return ProjectPhase.EXPANSION, f"Error determining phase: {str(e)}"

    def get_status_info(self) -> Dict[str, Any]:
        """Get current phase status information"""
        try:
            state = self.get_state()
            print(f"[DEBUG] get_status_info() - Current total_tokens: {state['total_tokens']}")
            
            # Calculate usage percentage
            usage_percent = (state['total_tokens'] / self.MODEL_TOKEN_LIMIT) * 100
            print(f"[DEBUG] get_status_info() - Usage percent: {usage_percent:.1f}%")
            
            # Determine status based on percentage
            if usage_percent >= self.CONVERGENCE_THRESHOLD * 100:
                status_icon = "🔴"
                status_message = "Convergence needed"
            elif usage_percent >= (self.CONVERGENCE_THRESHOLD * 0.9) * 100:
                status_icon = "⚠️"
                status_message = "Approaching convergence threshold"
            else:
                status_icon = "✓"
                status_message = "Below convergence threshold"
                
            # Calculate headroom based on phase
            if state['current_phase'] == ProjectPhase.EXPANSION:
                headroom = self.CONVERGENCE_TOKENS - state['total_tokens']
            else:
                headroom = self.MODEL_TOKEN_LIMIT - state['total_tokens']
                
            # Return consistent state
            return {
                "phase": state['current_phase'].value,
                "total_tokens": state['total_tokens'],
                "usage_percent": usage_percent,
                "status_icon": status_icon,
                "status_message": status_message,
                "headroom": headroom,
                "last_transition": state['last_transition'].isoformat()
            }
                
        except Exception as e:
            self.logger.log(f"Error getting status info: {str(e)}", 'error')
            # Return default values on error
            state = self.get_state()  # Get state even in error case
            return {
                "phase": state['current_phase'].value,
                "total_tokens": state['total_tokens'],
                "usage_percent": 0.0,
                "status_icon": "⚠️",
                "status_message": "Error getting status",
                "headroom": 0,
                "last_transition": state['last_transition'].isoformat()
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
