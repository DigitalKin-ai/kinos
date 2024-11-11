import ApiClient from './api-client.js';
import TeamService from './team-service.js';

class MissionService {
    constructor(baseUrl = '') {
        this.apiClient = new ApiClient('');  // Initialize with empty base URL for relative paths
        this.teamService = new TeamService(this);
        this.currentMission = null;
        this.missions = [];
        this.runningStates = new Map();
        this.connectionStatus = {
            connected: true,
            lastCheck: null,
            retryCount: 0
        };
    }

    getCurrentMission() {
        return this.currentMission;
    }

    getMissions() {
        return this.missions;
    }

    async _loadMissions() {
        try {
            const response = await this.apiClient.get('/missions');
            this.missions = response;
            return this.missions;
        } catch (error) {
            console.error('Error loading missions:', error);
            throw error;
        }
    }

    async selectMission(mission) {
        try {
            if (!mission?.id) {
                throw new Error('Invalid mission selected');
            }

            const response = await this.apiClient.post(`/api/missions/${mission.id}/select`);
            this.currentMission = response;
            return response;
        } catch (error) {
            console.error('Error selecting mission:', error);
            throw error;
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
            this.missions.forEach(mission => {
                this.runningStates.set(mission.id, false);
            });

            // Select first mission if available
            if (this.missions.length > 0) {
                await this.selectMission(this.missions[0]);
            }

            return this.missions;
        } catch (error) {
            console.error('Error initializing mission service:', error);
            throw error;
        }
    }

    // Other methods remain the same as in the previous implementation
    // (retryWithBackoff, checkServerConnection, etc.)
}

export default MissionService;
