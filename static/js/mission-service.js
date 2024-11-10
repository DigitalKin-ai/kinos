import ApiClient from './api-client.js';

class MissionService {
    constructor(baseUrl = '') {
        this.apiClient = new ApiClient(baseUrl);
        this.currentMission = null;
        this.missions = [];
        this.runningStates = new Map();
    }

    async initialize() {
        try {
            // Load all missions first
            const missions = await this.apiClient.getAllMissions();
            this.missions = missions;
            
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
