class MissionService {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    async getAllMissions() {
        try {
            const response = await fetch(`${this.baseUrl}/api/missions`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching missions:', error);
            throw error;
        }
    }

    async createMission(name, description = '') {
        try {
            const response = await fetch(`${this.baseUrl}/api/missions`, {
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
}

export default MissionService;
