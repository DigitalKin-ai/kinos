/**
 * API Client for KinOS
 * Centralizes all API calls and error handling
 */
class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = ''; // Always use relative paths
        this.token = null; // For future authentication
        this.retryCount = 0;
        this.maxRetries = 3;
    }

    async handleRequest(endpoint, options = {}) {
        let delay = 1000;
        for (let i = 0; i < this.maxRetries; i++) {
            try {
                const response = await fetch(endpoint, options);
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || `Server returned ${response.status}`);
                }
                return response;
            } catch (error) {
                if (i === this.maxRetries - 1) throw error;
                console.warn(`Attempt ${i + 1} failed, retrying in ${delay}ms...`);
                await new Promise(resolve => setTimeout(resolve, delay));
                delay *= 2; // Exponential backoff
            }
        }
    }

    async get(endpoint) {
        const response = await fetch(`${this.baseUrl}${endpoint}`);
        return this.handleResponse(response);
    }

    async post(endpoint, data = null) {
        const options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        try {
            // Always use relative paths starting with /api/
            const apiEndpoint = endpoint.startsWith('/') ? endpoint : `/api/${endpoint}`;
            const response = await this.handleRequest(apiEndpoint, options);
            return this.handleResponse(response);
        } catch (error) {
            console.error('API request failed:', error);
            throw new Error(`Failed to connect to server: ${error.message}`);
        }
    }

    async put(endpoint, data) {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        return this.handleResponse(response);
    }

    async delete(endpoint) {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'DELETE'
        });
        return this.handleResponse(response);
    }

    async checkServerConnection() {
        try {
            const response = await Promise.race([
                fetch('/api/status', {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    }
                }),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Request timeout')), 5000)
                )
            ]);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Server returned ${response.status}`);
            }

            const data = await response.json();
            return data.server?.running === true;
        } catch (error) {
            console.error('Server connection check failed:', error);
            throw error;
        }
    }

    async handleResponse(response) {
        if (!response.ok) {
            const error = await response.json();
            console.error('API Error:', error);
            
            // Create detailed error message with all available info
            let errorMessage = `${error.type || 'Error'}: ${error.error}\n`;
            if (error.details) {
                if (error.details.traceback) {
                    errorMessage += `\nTraceback:\n${error.details.traceback}`;
                }
                if (error.details.timestamp) {
                    errorMessage += `\nTimestamp: ${error.details.timestamp}`;
                }
                if (error.details.additional_info) {
                    errorMessage += `\nAdditional Info: ${JSON.stringify(error.details.additional_info)}`;
                }
            }
            
            // Display error in UI
            if (this.onError) {
                this.onError(errorMessage);
            }
            
            // Log full error object for debugging
            console.error('Full Error Details:', error);
            
            throw new Error(errorMessage);
        }
        return response.json();
    }

    async checkServerConnection() {
        try {
            const response = await Promise.race([
                fetch('/api/status', {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json'
                    }
                }),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Connection timeout')), 5000)
                )
            ]);

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            const data = await response.json();
            return data.server?.running === true;
        } catch (error) {
            console.error('Server connection check failed:', error);
            return false;
        }
    }

    setToken(token) {
        this.token = token;
    }

    async handleResponse(response) {
        if (!response.ok) {
            const error = await response.json();
            console.error('API Error:', error);
            
            // Create detailed error message with all available info
            let errorMessage = `${error.type || 'Error'}: ${error.error}\n`;
            if (error.details) {
                if (error.details.traceback) {
                    errorMessage += `\nTraceback:\n${error.details.traceback}`;
                }
                if (error.details.timestamp) {
                    errorMessage += `\nTimestamp: ${error.details.timestamp}`;
                }
                if (error.details.additional_info) {
                    errorMessage += `\nAdditional Info: ${JSON.stringify(error.details.additional_info)}`;
                }
            }
            
            // Display error in UI
            if (this.onError) {
                this.onError(errorMessage);
            }
            
            // Log full error object for debugging
            console.error('Full Error Details:', error);
            
            throw new Error(errorMessage);
        }
        return response.json();
    }

    // Agent endpoints
    async getAgentStatus() {
        const response = await fetch('/api/agents/status');
        return this.handleResponse(response);
    }

    async getAgentPrompt(agentId) {
        const response = await fetch(`/api/agent/${agentId}/prompt`);
        return this.handleResponse(response);
    }

    async saveAgentPrompt(agentId, prompt) {
        const response = await fetch(`/api/agents/${encodeURIComponent(agentId)}/prompt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        return this.handleResponse(response);
    }

    async controlAgent(agentId, action) {
        const response = await fetch(`/api/agent/${agentId}/${action}`, {
            method: 'POST'
        });
        return this.handleResponse(response);
    }

    // Mission endpoints
    async getAllMissions() {
        const response = await fetch('/api/missions');
        return this.handleResponse(response);
    }

    async createMission(name, description = '') {
        const response = await fetch('/api/missions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description })
        });
        return this.handleResponse(response);
    }

    async getMissionContent(missionId) {
        const response = await fetch(`/api/missions/${missionId}/content`);
        return this.handleResponse(response);
    }

    async updateMission(missionId, updates) {
        const response = await fetch(`/api/missions/${missionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        return this.handleResponse(response);
    }

    // File operations
    async getFileContent(missionId, filePath) {
        const response = await fetch(`/api/missions/${missionId}/files/${filePath}`);
        return this.handleResponse(response);
    }

    async saveFileContent(missionId, filePath, content) {
        const response = await fetch(`/api/missions/${missionId}/files/${filePath}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        return this.handleResponse(response);
    }

    // Agent operations
    async getAgentLogs(agentId) {
        const response = await fetch(`/api/agent/${agentId}/logs`);
        return this.handleResponse(response);
    }

    async updateAgentConfig(agentId, config) {
        const response = await fetch(`/api/agent/${agentId}/config`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        return this.handleResponse(response);
    }

    async createAgent(name, prompt) {
        const response = await fetch('/api/agents', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, prompt })
        });
        return this.handleResponse(response);
    }

    async selectMission(missionId) {
        try {
            // Validation des paramètres
            if (!missionId || isNaN(missionId)) {
                throw new Error('Invalid mission ID');
            }

            const response = await this.handleRequest(`/api/missions/${missionId}/select`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            // Vérifications supplémentaires
            if (!response.status || response.status !== 'success') {
                throw new Error(response.error || 'Mission selection failed');
            }

            // Événement personnalisé pour notifier le changement de mission
            const event = new CustomEvent('mission-selected', { 
                detail: { 
                    missionId, 
                    missionName: response.name 
                } 
            });
            window.dispatchEvent(event);

            return response;
        } catch (error) {
            console.error('Mission selection error:', error);
            
            // Événement d'erreur
            const errorEvent = new CustomEvent('mission-selection-error', { 
                detail: { 
                    error: error.message,
                    missionId 
                } 
            });
            window.dispatchEvent(errorEvent);

            throw error;
        }
    }

    async getMissionContent(missionId) {
        const response = await fetch(`/api/missions/${missionId}/content`);
        return this.handleResponse(response);
    }

    async createMission(name, description = '') {
        const response = await fetch(`/api/missions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description })
        });
        return this.handleResponse(response);
    }

    // Notification endpoints
    async getNotifications() {
        const response = await fetch('/api/notifications');
        return this.handleResponse(response);
    }

    async sendNotification(notification) {
        const response = await fetch('/api/notifications', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(notification)
        });
        return this.handleResponse(response);
    }
}

export default ApiClient;
