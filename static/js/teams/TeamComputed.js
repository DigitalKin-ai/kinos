export default {
    hasActiveTeam() {
        return this.activeTeam !== null;
    },
    getTeamMetrics() {
        return (teamId) => {
            if (!teamId) return null;

            const team = this.teams.find(t => t && t.id === teamId);
            if (!team) return null;

            const stats = this.teamStats.get(team.name);
            if (!stats) return {
                efficiency: 0,
                agentHealth: 0,
                completedTasks: 0,
                averageResponseTime: 0,
                errorRate: 0
            };

            return {
                efficiency: this.getTeamEfficiency(team) || 0,
                agentHealth: stats.agentStatus ? 
                    Object.values(stats.agentStatus)
                        .filter(agent => agent?.health?.is_healthy).length / (team.agents?.length || 1) : 0,
                completedTasks: stats.metrics?.completed_tasks || 0,
                averageResponseTime: stats.metrics?.average_response_time || 0,
                errorRate: stats.metrics?.error_rate || 0
            };
        };
    }
}
