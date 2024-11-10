import ApiClient from './api-client.js';

export default {
    methods: {
        async loadTeams() {
            try {
                if (!this.currentMission) {
                    console.warn('No mission selected');
                    this.teams = [];
                    return [];
                }
            
                const apiClient = new ApiClient();
                const response = await apiClient.getMissionTeams(this.currentMission.id);
                
                this.teams = Array.isArray(response) ? response.map(team => ({
                    ...team,
                    agents: team.agents || [],
                    status: team.status || 'available'
                })) : [];

                if (this.teams.length > 0 && !this.activeTeam) {
                    this.activeTeam = this.teams[0];
                }

                return this.teams;
            } catch (error) {
                console.error('Error loading teams:', error);
                this.teams = [];
                this.error = error.message;
                return [];
            }
        },

        getTeamMetrics(teamId) {
            if (!teamId) return null;
            
            const team = this.teams.find(t => t.id === teamId);
            if (!team) return null;
            
            return {
                totalAgents: team.agents?.length || 0,
                activeAgents: team.agents?.filter(a => a.status === 'active').length || 0,
                health: this.calculateTeamHealth(team)
            };
        },
        
        calculateTeamHealth(team) {
            if (!team || !team.agents || team.agents.length === 0) return 0;
            const healthyAgents = team.agents.filter(a => a.health?.is_healthy).length;
            return healthyAgents / team.agents.length;
        },

        async loadAgents() {
            try {
                this.loading = true;
                const apiClient = new ApiClient();
                
                const agents = await apiClient.get('/agents/list');
                const status = await apiClient.get('/agents/status');
                
                this.agents = agents.map(agent => ({
                    ...agent,
                    running: status[agent.id]?.running || false,
                    lastRun: status[agent.id]?.last_run || null,
                    status: status[agent.id]?.status || 'inactive'
                }));
                
                this.prompts = agents.reduce((acc, agent) => {
                    acc[agent.id] = agent.prompt;
                    return acc;
                }, {});
                
            } catch (error) {
                console.error('Failed to load agents:', error);
                this.error = error.message;
            } finally {
                this.loading = false;
            }
        },

        async toggleAgent(agent) {
            if (agent.loading) return;
            
            try {
                agent.loading = true;
                const apiClient = new ApiClient();
                const action = agent.running ? 'stop' : 'start';
                
                await apiClient.controlAgent(agent.id, action);
                agent.running = !agent.running;
                
            } catch (error) {
                console.error('Failed to toggle agent:', error);
                this.error = error.message;
            } finally {
                agent.loading = false;
            }
        }
    }
};
