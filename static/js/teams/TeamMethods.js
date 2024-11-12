export default {
    methods: {
        async loadTeams() {
            try {
                if (!this.currentMission?.id) {
                    this.teams.list = [];
                    return;
                }

                this.loading = true;
                const teams = await this.missionService.teamService.getTeamsForMission(this.currentMission.id);
            
                this.teams.list = teams.map(team => ({
                    ...team,
                    id: team.id || team.name.toLowerCase().replace(/\s+/g, '-'),
                    agents: team.agents || [],
                    status: team.status || 'available'
                }));

                if (this.teams.list.length > 0 && !this.teams.active) {
                    this.teams.active = this.teams.list[0];
                }
            } catch (error) {
                console.error('Failed to load teams:', error);
                this.teams.list = [];
                this.handleError('Failed to load teams', error);
            }
        },

        async toggleTeam(team) {
            if (this.loading.states.get(team.id)) return;
            
            try {
                await this.handleOperationWithRetry(
                    async () => {
                        if (!this.connectionStatus.connected) {
                            await this.checkConnection();
                            if (!this.connectionStatus.connected) {
                                throw new Error('Server is not available');
                            }
                        }

                        const action = this.isTeamRunning(team) ? 'stop' : 'start';
                        const response = await fetch(`/api/teams/${team.id}/${action}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' }
                        });
                        
                        if (!response.ok) throw new Error(`Failed to ${action} team`);
                        
                        const result = await response.json();
                        this.updateTeamState(team, result);
                    },
                    team.id,
                    `Failed to toggle team ${team.name}`
                );
            } catch (error) {
                console.error('Team toggle failed:', error);
                this.handleError(error.message);
            }
        },

        async activateTeam(team) {
            try {
                await this.stopCurrentAgents();
                await this.activateTeamAgents(team);
                await this.startAgents();
                
                this.updateTeamHistory(team, 'activated');
                this.startTeamMonitoring(team);
            } catch (error) {
                this.handleError('Failed to activate team', error);
            }
        },

        startTeamMonitoring(team) {
            this.initializeTeamStats(team);
            this.pollTeamStats(team);
            
            this.monitoring.statsInterval = setInterval(
                () => this.pollTeamStats(team), 
                this.monitoring.pollInterval
            );
        },

        stopTeamMonitoring() {
            if (this.monitoring.statsInterval) {
                clearInterval(this.monitoring.statsInterval);
                this.monitoring.statsInterval = null;
            }
        },

        async pollTeamStats(team) {
            try {
                const stats = await this.getTeamStatus(team);
                this.teams.stats.set(team.name, stats);
            } catch (error) {
                console.error('Error polling team stats:', error);
            }
        },

        async toggleAgent(teamName, agentName) {
            const agentKey = `${teamName}-${agentName}`;
            if (this.loading.agents.has(agentKey)) return;
            
            try {
                this.loading.agents.add(agentKey);
                const team = this.teams.list.find(t => t.name === teamName);
                if (!team) return;

                const isRunning = this.getAgentStatus(teamName, agentName);
                const action = isRunning ? 'stop' : 'start';

                const response = await fetch(
                    `/api/teams/${team.id}/agents/${agentName}/${action}`, 
                    { method: 'POST' }
                );

                if (!response.ok) throw new Error(`Failed to ${action} agent`);

                const result = await response.json();
                const stats = this.teams.stats.get(teamName) || {};
                if (!stats.agentStatus) stats.agentStatus = {};
                stats.agentStatus[agentName] = !isRunning;
                this.teams.stats.set(teamName, stats);

            } catch (error) {
                this.handleError(`Failed to toggle agent ${agentName}`, error);
            } finally {
                this.loading.agents.delete(agentKey);
            }
        },

        getAgentStatus(teamName, agentName) {
            const stats = this.teams.stats.get(teamName);
            return stats?.agentStatus?.[agentName] || false;
        },

        formatMetric(value, type) {
            const formatters = {
                percentage: value => `${Math.round(value)}%`,
                time: value => `${value.toFixed(1)}s`,
                number: value => Math.round(value).toString(),
                default: value => value
            };
            return (formatters[type] || formatters.default)(value);
        },

        updateTeamHistory(team, action) {
            if (!this.teams.history.has(team.name)) {
                this.teams.history.set(team.name, []);
            }
            this.teams.history.get(team.name).push({
                timestamp: new Date(),
                action
            });
        }
    }
}
