export default {
    data() {
        return {
            connectionStatus: {
                connected: true,
                lastCheck: null,
                retryCount: 0,
                checkInterval: null,
                maxRetries: 3,
                retryDelay: 1000,
                checkInProgress: false
            }
        }
    },
    methods: {
        async checkConnection() {
            if (this.connectionStatus.checkInProgress) return;
            
            try {
                this.connectionStatus.checkInProgress = true;
                const response = await fetch('/api/status', {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'X-Client-Timestamp': Date.now()
                    },
                    signal: AbortSignal.timeout(5000)
                });

                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}`);
                }

                const data = await response.json();
                this.connectionStatus.connected = true;
                this.connectionStatus.lastCheck = new Date();
                this.connectionStatus.retryCount = 0;
                
            } catch (error) {
                this.connectionStatus.connected = false;
                this.connectionStatus.retryCount++;
                this.handleConnectionError(error);
            } finally {
                this.connectionStatus.checkInProgress = false;
            }
        },

        startConnectionMonitoring() {
            this.stopConnectionMonitoring();
            
            this.checkConnection();
            
            this.connectionStatus.checkInterval = setInterval(() => {
                this.checkConnection();
            }, 30000);
        },

        stopConnectionMonitoring() {
            if (this.connectionStatus.checkInterval) {
                clearInterval(this.connectionStatus.checkInterval);
                this.connectionStatus.checkInterval = null;
            }
        },

        handleConnectionError(error) {
            const retryCount = this.connectionStatus.retryCount;
            const message = retryCount > 1 
                ? `Server connection lost. Retry attempt ${retryCount}...`
                : 'Server connection lost. Retrying...';
            
            this.$emit('connection-error', {
                title: 'Connection Error',
                message: message,
                type: 'connection',
                retry: true,
                details: error.message
            });

            const delay = Math.min(
                this.connectionStatus.retryDelay * Math.pow(2, retryCount - 1), 
                30000
            );

            if (retryCount < this.connectionStatus.maxRetries) {
                setTimeout(() => this.checkConnection(), delay);
            } else {
                this.$emit('connection-failed', {
                    message: 'Maximum retry attempts reached. Please check your connection.'
                });
            }
        }
    },
    beforeUnmount() {
        this.stopConnectionMonitoring();
    }
}
