"""Agent state tracking and metrics"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class AgentState:
    """Track agent state and metrics"""
    name: str
    status: str = 'waiting'  # waiting, active, completed, error
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3

    def mark_active(self):
        self.status = 'active'
        self.start_time = datetime.now()

    def mark_completed(self):
        self.status = 'completed'
        self.end_time = datetime.now()

    def mark_error(self, error: str):
        self.status = 'error'
        self.error = error
        self.retries += 1

    @property
    def can_retry(self) -> bool:
        return self.retries < self.max_retries

    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
