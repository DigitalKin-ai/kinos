import ApiClient from './api-client.js';

export default {
    methods: {
        async loadTeams() {
            try {
                if (!this.currentMission) {
                    this.teams = [];
                    return [];
                }
            
                const apiClient = new ApiClient();
                const response = await apiClient.getMissionTeams(this.currentMission.id);
                
                this.teams = (response || []).map(team => ({
                    ...team,
                    agents: team.agents || [],
                    status: team.status || 'available',
                    metrics: this.calculateTeamMetrics(team)
                }));

                if (this.teams.length > 0 && !this.activeTeam) {
                    this.activeTeam = this.teams[0];
                }

                return this.teams;
            } catch (error) {
                console.error('Error loading teams:', error);
                this.teams = [];
                this.error = error.message || 'Failed to load teams';
                return [];
            }
        },

        calculateTeamMetrics(team) {
            if (!team || !team.agents) return {
                totalAgents: 0,
                activeAgents: 0,
                healthPercentage: 0
            };

            const totalAgents = team.agents.length;
            const activeAgents = team.agents.filter(a => a.status === 'active').length;
            const healthyAgents = team.agents.filter(a => a.health?.is_healthy).length;

            return {
                totalAgents,
                activeAgents,
                healthPercentage: (healthyAgents / totalAgents) * 100
            };
        },

        async loadAgents() {
            try {
                this.loading = true;
                const apiClient = new ApiClient();
                
                const [agents, status] = await Promise.all([
                    apiClient.get('/agents/list'),
                    apiClient.get('/agents/status')
                ]);
                
                this.agents = agents.map(agent => ({
                    ...agent,
                    running: status[agent.id]?.running || false,
                    lastRun: status[agent.id]?.last_run || null,
                    status: status[agent.id]?.status || 'inactive',
                    health: status[agent.id]?.health || { is_healthy: false }
                }));
                
                this.metrics = {
                    totalAgents: this.agents.length,
                    activeAgents: this.agents.filter(a => a.running).length,
                    healthyAgents: this.agents.filter(a => a.health.is_healthy).length
                };
                
                this.prompts = agents.reduce((acc, agent) => {
                    acc[agent.id] = agent.prompt;
                    return acc;
                }, {});
                
            } catch (error) {
                console.error('Failed to load agents:', error);
                this.error = error.message || 'Failed to load agents';
                this.agents = [];
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
                agent.status = agent.running ? 'active' : 'inactive';
                
                this.updateAgentMetrics();
                
                this.$emit('agent-status-changed', {
                    id: agent.id,
                    running: agent.running
                });
                
            } catch (error) {
                console.error('Failed to toggle agent:', error);
                this.error = `Could not ${action} agent: ${error.message}`;
                
                this.$emit('notification', {
                    type: 'error',
                    message: this.error
                });
            } finally {
                agent.loading = false;
            }
        },

        updateAgentMetrics() {
            this.metrics = {
                totalAgents: this.agents.length,
                activeAgents: this.agents.filter(a => a.running).length,
                healthyAgents: this.agents.filter(a => a.health.is_healthy).length
            };
        }
    }
};
