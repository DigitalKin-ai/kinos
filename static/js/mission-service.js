import ApiClient from './api-client.js';
import TeamService from './team-service.js';

class MissionService {
    constructor(baseUrl = '') {
        this.apiClient = new ApiClient(baseUrl);
        this.teamService = new TeamService(this);
        this.currentMission = null;
        this.missions = [];
        this.runningStates = new Map();
    }

    async handleMissionOperation(operation, errorMessage) {
        try {
            return await this.retryWithBackoff(operation);
        } catch (error) {
            // Check if it's a connection error
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                this.serverStatus.connected = false;
                throw new Error('Server connection lost. Please check your connection and try again.');
            }
            throw error;
        }
    }

    startServerMonitoring() {
        // Check immediately
        this.checkServerStatus();
        // Then check every 30 seconds
        this.serverStatus.checkInterval = setInterval(() => {
            this.checkServerStatus();
        }, 30000);
    }

    stopServerMonitoring() {
        if (this.serverStatus.checkInterval) {
            clearInterval(this.serverStatus.checkInterval);
            this.serverStatus.checkInterval = null;
        }
    }

    async checkServerStatus() {
        try {
            const isConnected = await this.checkServerConnection();
            this.serverStatus.connected = isConnected;
            this.serverStatus.lastCheck = new Date();
        } catch (error) {
            this.serverStatus.connected = false;
            this.serverStatus.lastCheck = new Date();
            console.warn('Server connection check failed:', error);
        }
    }

    async initialize() {
        try {
            // Initialize both missions and teams
            await Promise.all([
                this._loadMissions(),
                this.teamService.initialize()
            ]);
            
            // Initialize running states
            missions.forEach(mission => {
                this.runningStates.set(mission.id, false);
            });

            // Select first mission if available
            if (missions.length > 0) {
                await this.selectMission(missions[0]);
            }

            return missions;
        } catch (error) {
            console.error('Error initializing mission service:', error);
            throw error;
        }
    }

    async selectMission(mission) {
        if (!mission?.id) {
            throw new Error('Invalid mission selected');
        }

        try {
            const wasRunning = this.runningStates.get(mission.id) || false;

            // Stop agents if running
            if (wasRunning) {
                await this.apiClient.controlAgent('stop');
                this.runningStates.set(mission.id, false);
            }

            // Select new mission
            const result = await this.apiClient.selectMission(mission.id);
            this.currentMission = result;

            return result;
        } catch (error) {
            console.error('Mission selection failed:', error);
            if (mission?.id) {
                this.runningStates.set(mission.id, false);
            }
            throw error;
        }
    }

    async createMission(name, description = '') {
        try {
            const mission = await this.apiClient.createMission(name, description);
            this.missions.push(mission);
            this.runningStates.set(mission.id, false);
            return mission;
        } catch (error) {
            console.error('Error creating mission:', error);
            throw error;
        }
    }

    async getMissionContent(missionId) {
        return await this.apiClient.getMissionContent(missionId);
    }

    async updateMission(missionId, updates) {
        const result = await this.apiClient.updateMission(missionId, updates);
        
        // Update local mission data
        const index = this.missions.findIndex(m => m.id === missionId);
        if (index !== -1) {
            this.missions[index] = {...this.missions[index], ...result};
        }
        
        return result;
    }

    getCurrentMission() {
        return this.currentMission;
    }

    getMissions() {
        return this.missions;
    }

    // Team management methods
    async getTeams(missionId) {
        return this.teamService.getTeamsForMission(missionId);
    }

    async selectTeam(missionId, teamId) {
        return this.teamService.activateTeam(missionId, teamId);
    }

    async getTeamStatus(missionId, teamId) {
        return this.teamService.getTeamStatus(teamId);
    }

    getActiveTeam() {
        return this.teamService.activeTeam;
    }

    async getTeams(missionId) {
        try {
            const response = await this.apiClient.get(`/missions/${missionId}/teams`);
            return response;
        } catch (error) {
            console.error('Error getting teams:', error);
            throw error;
        }
    }

    async selectTeam(missionId, teamId) {
        try {
            const response = await this.apiClient.post(`/missions/${missionId}/teams/${teamId}/select`);
            return response;
        } catch (error) {
            console.error('Error selecting team:', error);
            throw error;
        }
    }

    async getTeamStatus(missionId, teamId) {
        try {
            const response = await this.apiClient.get(`/missions/${missionId}/teams/${teamId}/status`);
            return response;
        } catch (error) {
            console.error('Error getting team status:', error);
            throw error;
        }
    }

    isRunning(missionId) {
        return this.runningStates.get(missionId) || false;
    }
}

export default MissionService;
