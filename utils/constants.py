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
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
TEMP_FILE_PREFIX = '.tmp_'
BACKUP_FILE_SUFFIX = '.bak'

# Agent configuration
MIN_INTERVAL = 60  # Minimum 1 minute
MAX_INTERVAL = 3600  # Maximum 1 hour
DEFAULT_INTERVAL = 120  # Default 2 minutes
AGENT_STARTUP_DELAY = 5  # Seconds between agent starts
AGENT_SHUTDOWN_TIMEOUT = 30  # Seconds to wait for agent shutdown

# Health monitoring
MAX_ERRORS = 5
HEALTH_CHECK_INTERVAL = 30
MAX_NO_CHANGES = 5
HEALTH_SCORE_THRESHOLD = 0.7
ERROR_BACKOFF_FACTOR = 1.5
RECOVERY_MAX_ATTEMPTS = 3

# Rate limiting
RATE_LIMIT_WINDOW = 60  # 1 minute
MAX_REQUESTS_PER_MINUTE = 50
RATE_LIMIT_BACKOFF_BASE = 30  # Base seconds for exponential backoff
RATE_LIMIT_MAX_BACKOFF = 300  # Maximum backoff in seconds

# Cache settings
CACHE_TTL = 3600  # 1 hour cache lifetime
MAX_CACHE_SIZE = 1000  # Maximum cache entries
CACHE_CLEANUP_INTERVAL = 300  # Cache cleanup every 5 minutes

# Thread management
THREAD_POOL_SIZE = 4
THREAD_TIMEOUT = 60
THREAD_MONITOR_INTERVAL = 10

# System resources
MIN_DISK_SPACE = 100 * 1024 * 1024  # 100MB minimum required
MAX_MEMORY_USAGE = 1024 * 1024 * 1024  # 1GB maximum memory usage
CPU_USAGE_THRESHOLD = 80  # Maximum CPU usage percentage

# Logging
LOG_ROTATION_SIZE = 10 * 1024 * 1024  # 10MB
MAX_LOG_FILES = 5
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Security
MAX_PATH_LENGTH = 260  # Maximum file path length
SECURE_PATH_REGEX = r'^[a-zA-Z0-9_\-./]+$'  # Allowed characters in paths
