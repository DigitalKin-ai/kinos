"""
Centralized constants for KinOS
"""

# System limits
MODEL_TOKEN_LIMIT = 128_000
CONVERGENCE_THRESHOLD = 0.60
EXPANSION_THRESHOLD = 0.50
DEFAULT_TIMEOUT = 300

# File operations
DEFAULT_ENCODING = 'utf-8'
MAX_RETRIES = 3
RETRY_DELAY = 1.0

# Agent configuration
MIN_INTERVAL = 60  # Minimum 1 minute
MAX_INTERVAL = 3600  # Maximum 1 hour
DEFAULT_INTERVAL = 120  # Default 2 minutes

# Health monitoring
MAX_ERRORS = 5
HEALTH_CHECK_INTERVAL = 30
MAX_NO_CHANGES = 5

# Rate limiting
RATE_LIMIT_WINDOW = 60  # 1 minute
MAX_REQUESTS_PER_MINUTE = 50
