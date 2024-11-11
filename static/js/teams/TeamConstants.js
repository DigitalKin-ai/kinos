export default {
    POLL_INTERVAL: 30000,
    STATUS_CACHE_TTL: 5000,
    MAX_RETRIES: 3,
    RETRY_DELAY: 1000,
    
    METRICS: {
        WEIGHTS: {
            SUCCESS: 0.4,
            SPEED: 0.3,
            TASKS: 0.3
        },
        THRESHOLDS: {
            HEALTH: {
                GOOD: 80,
                MEDIUM: 50
            },
            ERROR_RATE: {
                LOW: 10,
                MEDIUM: 25
            }
        }
    }
}
