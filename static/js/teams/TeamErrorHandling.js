export default {
    methods: {
        handleError(error, context = {}) {
            const errorMessage = typeof error === 'string' 
                ? error 
                : error.message || 'An unexpected error occurred';

            console.error(context.title || 'Error', errorMessage, context);

            this.errorMessage = errorMessage;
            this.showError = true;

            // Auto-hide error after 5 seconds
            setTimeout(() => {
                this.showError = false;
            }, 5000);

            // Optional: emit error for parent components
            this.$emit('error', { 
                title: context.title || 'Error', 
                message: errorMessage 
            });
        },

        async handleOperationWithRetry(operation, teamId, errorMessage, maxRetries = 3) {
            const attempts = this.retryAttempts.get(teamId) || 0;
            
            try {
                this.loadingStates.set(teamId, true);
                this.errorMessages.delete(teamId);
                
                return await operation();
                
            } catch (error) {
                console.error(`Operation failed for team ${teamId}:`, error);
                
                if (attempts < this.maxRetries) {
                    this.retryAttempts.set(teamId, attempts + 1);
                    await new Promise(resolve => setTimeout(resolve, this.retryDelay * Math.pow(2, attempts)));
                    return this.handleOperationWithRetry(operation, teamId, errorMessage);
                }
                
                this.errorMessages.set(teamId, errorMessage);
                this.handleError(error, { 
                    title: 'Operation Failed', 
                    teamId, 
                    errorMessage 
                });
                
                throw error;
            } finally {
                this.loadingStates.set(teamId, false);
            }
        }
    }
}
export default {
    methods: {
        handleError(error, context = {}) {
            const errorMessage = typeof error === 'string' 
                ? error 
                : error.message || 'An unexpected error occurred';

            console.error(context.title || 'Error', errorMessage, context);

            this.errorMessage = errorMessage;
            this.showError = true;

            // Auto-hide error after 5 seconds
            setTimeout(() => {
                this.showError = false;
            }, 5000);

            // Optional: emit error for parent components
            this.$emit('error', { 
                title: context.title || 'Error', 
                message: errorMessage 
            });
        },

        async handleOperationWithRetry(operation, teamId, errorMessage, maxRetries = 3) {
            const attempts = this.retryAttempts.get(teamId) || 0;
            
            try {
                this.loadingStates.set(teamId, true);
                this.errorMessages.delete(teamId);
                
                return await operation();
                
            } catch (error) {
                console.error(`Operation failed for team ${teamId}:`, error);
                
                if (attempts < this.maxRetries) {
                    this.retryAttempts.set(teamId, attempts + 1);
                    await new Promise(resolve => setTimeout(resolve, this.retryDelay * Math.pow(2, attempts)));
                    return this.handleOperationWithRetry(operation, teamId, errorMessage);
                }
                
                this.errorMessages.set(teamId, errorMessage);
                this.handleError(error, { 
                    title: 'Operation Failed', 
                    teamId, 
                    errorMessage 
                });
                
                throw error;
            } finally {
                this.loadingStates.set(teamId, false);
            }
        }
    }
}
