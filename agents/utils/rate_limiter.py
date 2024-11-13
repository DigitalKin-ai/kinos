"""
Rate limiting implementation
"""
import time
from typing import List, Optional, Dict, Any
from collections import deque

class RateLimiter:
    """Rate limiter using sliding window"""
    
    def __init__(self, max_requests: int, time_window: float):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed in window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: deque = deque()
        
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get rate limiter metrics
        
        Returns:
            Dict with usage metrics
        """
        now = time.time()
        
        # Remove expired timestamps
        while self.requests and self.requests[0] <= now - self.time_window:
            self.requests.popleft()
            
        return {
            'current_requests': len(self.requests),
            'max_requests': self.max_requests,
            'time_window': self.time_window,
            'usage_percent': (len(self.requests) / self.max_requests) * 100,
            'wait_time': self.get_wait_time()
        }

    def reset(self) -> None:
        """Reset rate limiter state"""
        self.requests.clear()

    def is_critical(self) -> bool:
        """
        Check if usage is at critical level
        
        Returns:
            bool: True if usage > 90%
        """
        return len(self.requests) >= (self.max_requests * 0.9)

    def get_backoff_time(self) -> float:
        """
        Get exponential backoff time based on usage
        
        Returns:
            float: Seconds to wait
        """
        usage_ratio = len(self.requests) / self.max_requests
        if usage_ratio > 0.9:
            return min(300, 2 ** (usage_ratio * 10))  # Max 5 minutes
        return 0

    def should_allow_request(self) -> bool:
        """
        Check if request should be allowed
        
        Returns:
            bool: True if request is allowed
        """
        now = time.time()
        
        # Remove expired timestamps
        while self.requests and self.requests[0] <= now - self.time_window:
            self.requests.popleft()
            
        # Check if under limit
        return len(self.requests) < self.max_requests
        
    def record_request(self):
        """Record a request timestamp"""
        self.requests.append(time.time())
        
    def get_wait_time(self) -> float:
        """
        Get time to wait before next request
        
        Returns:
            float: Seconds to wait
        """
        if not self.requests:
            return 0
            
        now = time.time()
        oldest = self.requests[0]
        
        # Calculate when oldest request expires
        expires = oldest + self.time_window
        
        # Return time to wait
        wait_time = expires - now
        return max(0, wait_time)
