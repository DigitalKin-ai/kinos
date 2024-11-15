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
    
    def get_model_token_limit(self) -> int:
        """Get token limit for current model"""
        try:
            from services import init_services
            services = init_services(None)
            model_router = services['model_router']
            
            # Model-specific limits
            limits = {
                "claude-3-5-sonnet-20241022": 150000,
                "claude-3-5-haiku-20241022": 128000,
                "gpt-4o": 128000,
                "gpt-4o-mini": 128000
            }
            
            return limits.get(model_router.current_model, 128000)  # Default to 128k
            
        except Exception:
            return 128000  # Conservative default

    # Class constants
    CONVERGENCE_THRESHOLD = 0.60
    EXPANSION_THRESHOLD = 0.50

    @property
    def MODEL_TOKEN_LIMIT(self) -> int:
        return self.get_model_token_limit()

    @property 
    def CONVERGENCE_TOKENS(self) -> int:
        return int(self.MODEL_TOKEN_LIMIT * self.CONVERGENCE_THRESHOLD)

    @property
    def EXPANSION_TOKENS(self) -> int:
        return int(self.MODEL_TOKEN_LIMIT * self.EXPANSION_THRESHOLD)

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
            state = self.get_state()
            state['total_tokens'] = max(0, total_tokens)  # Ensure non-negative
            old_phase = state['current_phase']
            usage_percent = (state['total_tokens'] / self.MODEL_TOKEN_LIMIT) * 100
            
            if usage_percent >= self.CONVERGENCE_THRESHOLD * 100:
                new_phase = ProjectPhase.CONVERGENCE
                message = f"Convergence needed - Token usage at {usage_percent:.1f}%"
            else:
                new_phase = ProjectPhase.EXPANSION
                message = f"Expansion phase - Token usage at {usage_percent:.1f}%"
            
            if new_phase != old_phase:
                state['current_phase'] = new_phase
                state['last_transition'] = datetime.now()
            else:
                state['current_phase'] = new_phase
            
            return new_phase, message

        except Exception as e:
            self.logger.log(f"Error determining phase: {str(e)}", 'error')
            return ProjectPhase.EXPANSION, f"Error determining phase: {str(e)}"

    def get_status_info(self) -> Dict[str, Any]:
        """Get current phase status information"""
        try:
            state = self.get_state()
            usage_percent = (state['total_tokens'] / self.MODEL_TOKEN_LIMIT) * 100
            
            if usage_percent >= self.CONVERGENCE_THRESHOLD * 100:
                status_icon = "🔴"
                status_message = "Convergence needed"
            elif usage_percent >= (self.CONVERGENCE_THRESHOLD * 0.9) * 100:
                status_icon = "⚠️"
                status_message = "Approaching convergence threshold"
            else:
                status_icon = "✓"
                status_message = "Below convergence threshold"
                
            if state['current_phase'] == ProjectPhase.EXPANSION:
                headroom = self.CONVERGENCE_TOKENS - state['total_tokens']
            else:
                headroom = self.MODEL_TOKEN_LIMIT - state['total_tokens']
                
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
            state = self.get_state()
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

    def get_phase_weights(self, phase: str) -> Dict[str, float]:
        """Get agent weights for current phase"""
        try:
            # Get team service
            from services import init_services
            services = init_services(None)
            team_service = services['team_service']
            
            # Get active team config
            active_team = None
            for team in team_service.predefined_teams:
                if team.get('phase_config', {}).get(phase.lower()):
                    active_team = team
                    break
                    
            if not active_team:
                return {}
                
            # Get phase config
            phase_config = active_team['phase_config'][phase.lower()]
            
            # Build weights dictionary
            weights = {}
            for agent in phase_config.get('active_agents', []):
                if isinstance(agent, dict):
                    weights[agent['name']] = agent.get('weight', 0.5)
                else:
                    weights[agent] = 0.5
                    
            return weights
            
        except Exception as e:
            self.logger.log(f"Error getting phase weights: {str(e)}", 'error')
            return {}
