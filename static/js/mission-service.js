import ApiClient from './api-client.js';

class MissionService {
    constructor(baseUrl = '') {
        this.apiClient = new ApiClient(baseUrl);
    }

    async getAllMissions() {
        try {
            return await this.apiClient.getAllMissions();
        } catch (error) {
            console.error('Error fetching missions:', error);
            throw error;
        }
    }

    async createMission(name, description = '') {
        try {
            const response = await fetch('/api/missions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, description })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to create mission');
            }

            return await response.json();
        } catch (error) {
            console.error('Error creating mission:', error);
            throw error;
        }
    }

    async getMissionContent(missionId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/missions/${missionId}/content`);
            if (!response.ok) {
                throw new Error('Failed to load mission content');
            }
            return await response.json();
        } catch (error) {
            console.error('Error loading mission content:', error);
            throw error;
        }
    }

    async updateMission(missionId, updates) {
        try {
            const response = await fetch(`${this.baseUrl}/api/missions/${missionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updates)
            });

            if (!response.ok) {
                throw new Error('Failed to update mission');
            }

            return await response.json();
        } catch (error) {
            console.error('Error updating mission:', error);
            throw error;
        }
    }

    async selectMission(mission) {
        try {
            const response = await fetch(`/api/missions/${mission.id}/select`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to select mission');
            }

            const result = await response.json();
            console.log('Mission selected successfully:', result);
            return result;
        } catch (error) {
            console.error('Error selecting mission:', error);
            throw error;
        }
    }
}

export default MissionService;
