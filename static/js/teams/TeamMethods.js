export default {
    methods: {
        async loadTeams() {
            try {
                if (!this.currentMission?.id) {
                    this.teams = [];
                    return;
                }

                const teams = await this.missionService.teamService.getTeamsForMission(this.currentMission.id);
                
                this.teams = teams.map(team => ({
                    ...team,
                    id: team.id || team.name.toLowerCase().replace(/\s+/g, '-'),
                    agents: team.agents || [],
                    status: team.status || 'available'
                }));

                if (this.teams.length > 0 && !this.activeTeam) {
                    this.activeTeam = this.teams[0];
                }
            } catch (error) {
                console.error('Failed to load teams:', error);
                this.teams = [];
                this.handleError('Failed to load teams', error);
            }
        },

        async toggleTeam(team) {
            if (this.loadingStates.get(team.id)) return;
            
            try {
                await this.handleOperationWithRetry(
                    async () => {
                        const action = this.isTeamRunning(team) ? 'stop' : 'start';
                        const response = await fetch(`/api/teams/${team.id}/${action}`, {
                            method: 'POST'
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
        }
    }
}
