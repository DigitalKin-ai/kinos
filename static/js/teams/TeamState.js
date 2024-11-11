export default function() {
    return {
        statusCacheTTL: 5000,
        showAddAgentModal: false,
        loadingStates: new Map(),
        error: null,
        errorMessage: null,
        showError: false,
        connectionStatus: {
            connected: true,
            lastCheck: null,
            retryCount: 0
        },
        connectionCheckInProgress: false,
        errorMessages: new Map(),
        retryAttempts: new Map(),
        maxRetries: 3,
        retryDelay: 1000,
        loading: false,
        availableAgents: [
            "SpecificationsAgent", "ManagementAgent", "EvaluationAgent",
            "SuiviAgent", "DocumentalisteAgent", "DuplicationAgent",
            "RedacteurAgent", "ProductionAgent", "TesteurAgent", "ValidationAgent"
        ],
        selectedTeamForEdit: null,
        selectedAgent: null,
        teams: [], 
        activeTeam: null,
        teamStats: new Map(),
        teamHistory: new Map(),
        loadingStats: false,
        statsInterval: null,
        POLL_INTERVAL: 30000,
        loadingTeams: new Set(),
        loadingAgents: new Set(),
        statusCache: new Map(),
        statusCacheTTL: 5000
    }
}
