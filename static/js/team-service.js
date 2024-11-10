export default class TeamService {
    constructor(missionService) {
        this.missionService = missionService;
        this.teams = new Map();
        this.activeTeam = null;
        this.teamStates = new Map();
        this.connectionStatus = {
            connected: true,
            lastCheck: null,
            retryCount: 0
        };
        this.statusCache = new Map();
        this.statusCacheTTL = 5000; // 5 seconds
    }

    async initialize() {
        // Load predefined team configurations
        this.predefinedTeams = [
            {
                id: 'book-writing',
                name: "Book Writing Team",
                agents: [
                    "SpecificationsAgent",
                    "ManagementAgent",
                    "EvaluationAgent",
                    "SuiviAgent",
                    "DocumentalisteAgent",
                    "DuplicationAgent",
                    "RedacteurAgent",
                    "ValidationAgent"
                ]
            },
            {
                id: 'literature-review',
                name: "Literature Review Team",
                agents: [
                    "SpecificationsAgent",
                    "ManagementAgent",
                    "EvaluationAgent",
                    "SuiviAgent",
                    "DocumentalisteAgent",
                    "DuplicationAgent",
                    "RedacteurAgent",
                    "ValidationAgent"
                ]
            },
            {
                id: 'coding',
                name: "Coding Team",
                agents: [
                    "SpecificationsAgent",
                    "ManagementAgent",
                    "EvaluationAgent",
                    "SuiviAgent",
                    "DocumentalisteAgent",
                    "DuplicationAgent",
                    "ProductionAgent",
                    "TesteurAgent",
                    "ValidationAgent"
                ]
            }
        ];
        
        // Initialize connection monitoring
        await this.checkConnection();
        this.startConnectionMonitoring();
    }

    async checkConnection() {
        try {
            const response = await fetch('/api/status');
            this.connectionStatus.connected = response.ok;
            this.connectionStatus.lastCheck = new Date();
            this.connectionStatus.retryCount = 0;
            return response.ok;
        } catch (error) {
            this.connectionStatus.connected = false;
            this.connectionStatus.retryCount++;
            console.error('Connection check failed:', error);
            return false;
        }
    }

    startConnectionMonitoring() {
        setInterval(() => this.checkConnection(), 30000); // Check every 30 seconds
    }

    cleanup() {
        if (this.connectionInterval) {
            clearInterval(this.connectionInterval);
        }
        this.teams.clear();
        this.teamStates.clear();
        this.statusCache?.clear();
    }

    async getTeamsForMission(missionId) {
        try {
            const response = await fetch(`/api/missions/${encodeURIComponent(missionId)}/teams`);
            if (!response.ok) throw new Error('Failed to fetch teams');
            const teams = await response.json();
            
            // Update local cache
            teams.forEach(team => this.teams.set(team.id, team));
            
            return teams;
        } catch (error) {
            console.error('Error fetching teams:', error);
            throw error;
        }
    }

    async activateTeam(missionId, teamId) {
        try {
            // Stop current active team if exists
            if (this.activeTeam) {
                await this.deactivateTeam(this.activeTeam.id);
            }

            const response = await fetch(`/api/missions/${encodeURIComponent(missionId)}/teams/${encodeURIComponent(teamId)}/activate`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Failed to activate team');
            
            const team = await response.json();
            this.activeTeam = team;
            this.teamStates.set(teamId, { active: true, timestamp: Date.now() });
            
            return team;
        } catch (error) {
            console.error('Error activating team:', error);
            throw error;
        }
    }

    async deactivateTeam(teamId) {
        try {
            const response = await fetch(`/api/teams/${encodeURIComponent(teamId)}/deactivate`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Failed to deactivate team');
            
            this.teamStates.set(teamId, { active: false, timestamp: Date.now() });
            if (this.activeTeam?.id === teamId) {
                this.activeTeam = null;
            }
            
            return true;
        } catch (error) {
            console.error('Error deactivating team:', error);
            throw error;
        }
    }

    async getTeamStatus(teamId) {
        try {
            const response = await fetch(`/api/teams/${encodeURIComponent(teamId)}/status`);
            if (!response.ok) throw new Error('Failed to fetch team status');
            
            const status = await response.json();
            this.teamStates.set(teamId, {
                ...status,
                timestamp: Date.now()
            });
            
            return status;
        } catch (error) {
            console.error('Error fetching team status:', error);
            throw error;
        }
    }

    async addAgentToTeam(teamId, agentId) {
        try {
            const response = await fetch(`/api/teams/${teamId}/agents`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ agentId })
            });

            if (!response.ok) throw new Error('Failed to add agent to team');
            
            const updatedTeam = await response.json();
            this.teams.set(teamId, updatedTeam);
            
            return updatedTeam;
        } catch (error) {
            console.error('Error adding agent to team:', error);
            throw error;
        }
    }

    async removeAgentFromTeam(teamId, agentId) {
        try {
            const response = await fetch(`/api/teams/${teamId}/agents/${agentId}`, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error('Failed to remove agent from team');
            
            const updatedTeam = await response.json();
            this.teams.set(teamId, updatedTeam);
            
            return updatedTeam;
        } catch (error) {
            console.error('Error removing agent from team:', error);
            throw error;
        }
    }

    getTeamEfficiency(teamId) {
        const team = this.teams.get(teamId);
        if (!team) return 0;

        const status = this.teamStates.get(teamId);
        if (!status) return 0;

        // Calculate efficiency based on multiple metrics
        const metrics = {
            agentHealth: this._calculateAgentHealth(team, status),
            taskCompletion: this._calculateTaskCompletion(status),
            responseTime: this._calculateResponseTime(status),
            errorRate: this._calculateErrorRate(status)
        };

        // Weight different metrics
        const weights = {
            agentHealth: 0.4,
            taskCompletion: 0.3,
            responseTime: 0.2,
            errorRate: 0.1
        };

        // Calculate final score
        return Object.entries(metrics).reduce((score, [key, value]) => {
            return score + (value * weights[key]);
        }, 0);
    }

    // Private methods for metric calculations
    _calculateAgentHealth(team, status) {
        if (!status.agentStatus) return 0;
        const healthyAgents = Object.values(status.agentStatus)
            .filter(agent => agent.health?.is_healthy).length;
        return healthyAgents / team.agents.length;
    }

    _calculateTaskCompletion(status) {
        return status.metrics?.completed_tasks / 100 || 0;
    }

    _calculateResponseTime(status) {
        const avgTime = status.metrics?.average_response_time || 0;
        const maxAcceptableTime = 5000; // 5 seconds
        return Math.max(0, 1 - (avgTime / maxAcceptableTime));
    }

    _calculateErrorRate(status) {
        const errorRate = status.metrics?.error_rate || 0;
        return Math.max(0, 1 - errorRate);
    }
}
