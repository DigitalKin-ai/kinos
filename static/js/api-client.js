/**
 * API Client for KinOS
 * Centralizes all API calls and error handling
 */
class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.token = null; // For future authentication
    }

    setToken(token) {
        this.token = token;
    }

    async handleResponse(response) {
        if (!response.ok) {
            const error = await response.json();
            // Handle different error codes
            switch(response.status) {
                case 401:
                    throw new Error('Unauthorized');
                case 404:
                    throw new Error('Resource not found');
                default:
                    throw new Error(error.error || 'API request failed');
            }
        }
        return response.json();
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
        const response = await fetch(`${this.baseUrl}/api/agent/${agentId}/prompt`, {
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
