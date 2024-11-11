export default {
    methods: {
        getTeamEfficiency(team) {
            const stats = this.teamStats.get(team.name);
            if (!stats) return 0;
            
            const successWeight = 0.4;
            const speedWeight = 0.3;
            const taskWeight = 0.3;

            const successRate = Math.min(Math.max(stats.successRate || 0, 0), 100);
            const responseTime = Math.min(Math.max(stats.averageResponseTime || 0, 0), 1000);
            const tasks = Math.min(Math.max(stats.completedTasks || 0, 0), 100);

            const successScore = successRate * successWeight;
            const speedScore = (1000 - responseTime) / 1000 * speedWeight;
            const taskScore = tasks / 100 * taskWeight;

            return Math.min(Math.max((successScore + speedScore + taskScore) * 100, 0), 100);
        },

        formatMetric(value, type) {
            const formatters = {
                percentage: value => `${Math.round(value)}%`,
                time: value => `${value.toFixed(1)}s`,
                number: value => Math.round(value).toString(),
                default: value => value
            };

            return (formatters[type] || formatters.default)(value);
        }
    }
}
