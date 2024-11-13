"""Health monitoring utilities"""
from typing import Dict, Any
from datetime import datetime

class HealthManager:
    """Manages health monitoring and metrics"""
    
    def __init__(self, agent):
        """Initialize with agent reference"""
        self.agent = agent
        
    def is_healthy(self) -> bool:
        """Check if agent is in healthy state"""
        try:
            if self.agent.last_run:
                time_since_last = (datetime.now() - self.agent.last_run).total_seconds()
                if time_since_last > 120:  # 2 minutes
                    return False
                    
            if self.agent.consecutive_no_changes > 5:
                return False
                
            return True
            
        except Exception as e:
            self.agent.logger.log(f"Error checking health: {str(e)}", 'error')
            return False
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive health metrics"""
        try:
            return {
                'status': {
                    'running': self.agent.running,
                    'is_healthy': self.is_healthy(),
                    'last_run': self.agent.last_run.isoformat() if self.agent.last_run else None,
                    'last_change': self.agent.last_change.isoformat() if self.agent.last_change else None
                },
                'performance': {
                    'consecutive_no_changes': self.agent.consecutive_no_changes,
                    'current_interval': self.agent.calculate_dynamic_interval(),
                    'error_count': getattr(self.agent, 'error_count', 0)
                },
                'resources': {
                    'mission_files': len(self.agent.mission_files),
                    'cache_size': len(self.agent._prompt_cache),
                    'working_dir': self.agent.mission_dir
                }
            }
        except Exception as e:
            self.agent.logger.log(f"Error getting health metrics: {str(e)}", 'error')
            return {
                'error': str(e),
                'status': {'running': False, 'is_healthy': False}
            }
            
    def calculate_health_score(self) -> float:
        """Calculate overall health score"""
        try:
            metrics = self.get_metrics()
            
            # Weight different factors
            weights = {
                'is_healthy': 0.4,
                'error_rate': 0.3,
                'performance': 0.3
            }
            
            # Calculate component scores
            health_score = 1.0 if metrics['status']['is_healthy'] else 0.0
            error_score = 1.0 - (metrics['performance']['error_count'] / 100)  # Cap at 100 errors
            perf_score = 1.0 - (metrics['performance']['consecutive_no_changes'] / 10)  # Cap at 10
            
            # Calculate weighted average
            total_score = (
                weights['is_healthy'] * health_score +
                weights['error_rate'] * error_score +
                weights['performance'] * perf_score
            )
            
            return max(0.0, min(1.0, total_score))
            
        except Exception as e:
            self.agent.logger.log(f"Error calculating health score: {str(e)}", 'error')
            return 0.0
