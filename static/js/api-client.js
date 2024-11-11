/**
 * API Client for KinOS
 * Centralizes all API calls and error handling
 */
class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.connectionState = {
            isOnline: navigator.onLine,
            lastCheckTimestamp: null,
            connectionErrors: 0
        };

        // Add connection event listeners
        window.addEventListener('online', this.handleOnline.bind(this));
        window.addEventListener('offline', this.handleOffline.bind(this));

        // Écouteurs d'événements de connexion
        window.addEventListener('online', this.handleOnline.bind(this));
        window.addEventListener('offline', this.handleOffline.bind(this));
    }

    handleOnline() {
        this.connectionState.isOnline = true;
        this.connectionState.connectionErrors = 0;
        this.notifyConnectionChange('online');
    }

    handleOffline() {
        this.connectionState.isOnline = false;
        this.notifyConnectionChange('offline');
    }

    notifyConnectionChange(status) {
        const event = new CustomEvent('connection-status-change', {
            detail: { 
                status, 
                timestamp: new Date() 
            }
        });
        window.dispatchEvent(event);
    }

    async selectMission(missionId) {
        console.log(`Attempting to select mission ${missionId}`);
        
        // Vérification de la connexion avant la requête
        if (!this.connectionState.isOnline) {
            throw new Error('No internet connection');
        }

        try {
            // Configuration de la requête avec gestion avancée
            const requestConfig = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Client-Timestamp': Date.now(),
                    'X-Client-Version': '1.0.0',
                    'X-Debug-Request': 'true'  // Add a debug header
                },
                timeout: 10000  // 10 secondes
            };

            // Requête avec gestion des erreurs
            const response = await this.post(`/api/missions/${missionId}/select`, null, {
                ...requestConfig,
                retryStrategy: {
                    maxRetries: 3,
                    baseDelay: 1000,
                    backoffFactor: 2
                },
                errorHandling: {
                    MISSION_NOT_FOUND: this.handleMissionNotFound,
                    AGENT_INIT_FAILED: this.handleAgentInitError,
                    UNEXPECTED_ERROR: this.handleUnexpectedError
                }
            });

            console.log('Mission selection response:', response);

            // Événement de succès
            const successEvent = new CustomEvent('mission-selected', {
                detail: {
                    missionId,
                    missionName: response.name,
                    selectedAt: response.selected_at,
                    resources: response.resources
                }
            });
            window.dispatchEvent(successEvent);

            return response;
        } catch (error) {
            // Gestion centralisée des erreurs
            this.handleMissionSelectionError(error);
            throw error;
        }
    }

    handleMissionSelectionError(error) {
        // Analyse et catégorisation de l'erreur
        const errorCategories = {
            'No internet connection': this.handleOfflineError,
            'Mission not found': this.handleMissionNotFoundError,
            'Timeout': this.handleTimeoutError
        };

        const errorHandler = errorCategories[error.message] || this.handleGenericError;
        errorHandler.call(this, error);

        // Mise à jour des métriques de connexion
        this.updateConnectionMetrics(error);
    }

    updateConnectionMetrics(error) {
        this.connectionState.connectionErrors++;
        this.connectionState.lastCheckTimestamp = Date.now();

        // Événement pour suivre les erreurs de connexion
        const connectionErrorEvent = new CustomEvent('connection-error', {
            detail: {
                error,
                connectionState: this.connectionState
            }
        });
        window.dispatchEvent(connectionErrorEvent);
    }

    async get(endpoint) {
        const apiEndpoint = endpoint.startsWith('/') ? endpoint : `/api/${endpoint}`;
        const response = await fetch(`${this.baseUrl}${apiEndpoint}`);
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
            const response = await fetch(`${this.baseUrl}${apiEndpoint}`, options);
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
                fetch(`${this.baseUrl}/api/status`, {
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
        try {
            // More comprehensive error parsing
            if (!response.ok) {
                const errorText = await response.text();
                let errorDetails = {
                    status: response.status,
                    statusText: response.statusText,
                    message: 'Unknown server error'
                };

                try {
                    // Try to parse JSON error
                    const errorJson = JSON.parse(errorText);
                    errorDetails = {
                        ...errorDetails,
                        ...errorJson
                    };
                } catch {
                    // Fallback to raw error text
                    errorDetails.message = errorText || errorDetails.message;
                }

                throw new Error(JSON.stringify(errorDetails));
            }

            // Check for empty response
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.warn('Non-JSON response:', text);
                return text;
            }
        
            const data = await response.json();
            console.log('Parsed response data:', data);
            return data;
        } catch (error) {
            console.error('Response handling error:', error);
            throw error;
        }
    }

    setToken(token) {
        this.token = token;
    }

    // Agent endpoints
    async getAgentStatus() {
        const response = await fetch(`${this.baseUrl}/api/agents/status`);
        return this.handleResponse(response);
    }

    async getAgentPrompt(agentId) {
        const response = await fetch(`${this.baseUrl}/api/agent/${agentId}/prompt`);
        return this.handleResponse(response);
    }

    async saveAgentPrompt(agentId, prompt) {
        const response = await fetch(`${this.baseUrl}/api/agents/${encodeURIComponent(agentId)}/prompt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        return this.handleResponse(response);
    }

    async controlAgent(agentId, action) {
        const response = await fetch(`${this.baseUrl}/api/agent/${agentId}/${action}`, {
            method: 'POST'
        });
        return this.handleResponse(response);
    }

    // Mission endpoints
    async getAllMissions() {
        const response = await fetch(`${this.baseUrl}/api/missions`);
        return this.handleResponse(response);
    }

    async createMission(name, description = '') {
        const response = await fetch(`${this.baseUrl}/api/missions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description })
        });
        return this.handleResponse(response);
    }

    async getMissionContent(missionId) {
        const response = await fetch(`${this.baseUrl}/api/missions/${missionId}/content`);
        return this.handleResponse(response);
    }

    async getMissionTeams(missionId) {
        const response = await fetch(`${this.baseUrl}/api/missions/${missionId}/teams`);
        return this.handleResponse(response);
    }

    async updateMission(missionId, updates) {
        const response = await fetch(`${this.baseUrl}/api/missions/${missionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        return this.handleResponse(response);
    }

    // File operations
    async getFileContent(missionId, filePath) {
        const response = await fetch(`${this.baseUrl}/api/missions/${missionId}/files/${filePath}`);
        return this.handleResponse(response);
    }

    async saveFileContent(missionId, filePath, content) {
        const response = await fetch(`${this.baseUrl}/api/missions/${missionId}/files/${filePath}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        return this.handleResponse(response);
    }

    // Agent operations
    async getAgentLogs(agentId) {
        const response = await fetch(`${this.baseUrl}/api/agent/${agentId}/logs`);
        return this.handleResponse(response);
    }

    async updateAgentConfig(agentId, config) {
        const response = await fetch(`${this.baseUrl}/api/agent/${agentId}/config`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        return this.handleResponse(response);
    }

    async createAgent(name, prompt) {
        const response = await fetch(`${this.baseUrl}/api/agents`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, prompt })
        });
        return this.handleResponse(response);
    }


    // Notification endpoints
    async getNotifications() {
        const response = await fetch(`${this.baseUrl}/api/notifications`);
        return this.handleResponse(response);
    }

    async sendNotification(notification) {
        const response = await fetch(`${this.baseUrl}/api/notifications`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(notification)
        });
        return this.handleResponse(response);
    }
}

export default ApiClient;
