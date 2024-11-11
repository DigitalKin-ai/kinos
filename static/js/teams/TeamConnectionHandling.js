export default {
    methods: {
        async checkConnection() {
            if (this.connectionCheckInProgress) return;
            
            try {
                this.connectionCheckInProgress = true;
                const response = await fetch('/api/status');
                
                this.connectionStatus.connected = response.ok;
                this.connectionStatus.lastCheck = new Date();
                this.connectionStatus.retryCount = 0;
                
            } catch (error) {
                this.connectionStatus.connected = false;
                this.connectionStatus.retryCount++;
                this.handleConnectionError(error);
            } finally {
                this.connectionCheckInProgress = false;
            }
        },

        startConnectionMonitoring() {
            this.checkConnection();
            this.connectionInterval = setInterval(() => {
                this.checkConnection();
            }, 30000); // Check every 30 seconds
        },

        stopConnectionMonitoring() {
            if (this.connectionInterval) {
                clearInterval(this.connectionInterval);
                this.connectionInterval = null;
            }
        },

        handleConnectionError(error) {
            const retryCount = this.connectionStatus.retryCount;
            const message = retryCount > 1 
                ? `Connection lost. Retry attempt ${retryCount}...`
                : 'Connection lost. Retrying...';
            
            this.handleError({
                title: 'Connection Error',
                message: message,
                type: 'connection',
                retry: true,
                details: error.message
            });

            const delay = Math.min(1000 * Math.pow(2, retryCount - 1), 30000);
            setTimeout(() => this.checkConnection(), delay);
        }
    }
}
export default {
    methods: {
        async checkConnection() {
            if (this.connectionCheckInProgress) return;
            
            try {
                this.connectionCheckInProgress = true;
                const response = await fetch('/api/status');
                
                this.connectionStatus.connected = response.ok;
                this.connectionStatus.lastCheck = new Date();
                this.connectionStatus.retryCount = 0;
                
            } catch (error) {
                this.connectionStatus.connected = false;
                this.connectionStatus.retryCount++;
                this.handleConnectionError(error);
            } finally {
                this.connectionCheckInProgress = false;
            }
        },

        startConnectionMonitoring() {
            this.checkConnection();
            this.connectionInterval = setInterval(() => {
                this.checkConnection();
            }, 30000); // Check every 30 seconds
        },

        stopConnectionMonitoring() {
            if (this.connectionInterval) {
                clearInterval(this.connectionInterval);
                this.connectionInterval = null;
            }
        },

        handleConnectionError(error) {
            const retryCount = this.connectionStatus.retryCount;
            const message = retryCount > 1 
                ? `Connection lost. Retry attempt ${retryCount}...`
                : 'Connection lost. Retrying...';
            
            this.handleError({
                title: 'Connection Error',
                message: message,
                type: 'connection',
                retry: true,
                details: error.message
            });

            const delay = Math.min(1000 * Math.pow(2, retryCount - 1), 30000);
            setTimeout(() => this.checkConnection(), delay);
        }
    }
}
