export default function() {
    return {
        // États de connexion
        connection: {
            status: {
                connected: true,
                lastCheck: null,
                retryCount: 0
            },
            checkInProgress: false,
            interval: null
        },

        // États de chargement
        loading: {
            teams: false,
            agents: new Set(),
            states: new Map()
        },

        // États des équipes
        teams: {
            list: [],
            active: null,
            stats: new Map(),
            history: new Map(),
            statusCache: new Map(),
            statusCacheTTL: 5000
        },

        // États des agents
        agents: {
            available: [
                "SpecificationsAgent", "ManagementAgent", "EvaluationAgent",
                "ChroniqueurAgent", "DocumentalisteAgent", "DuplicationAgent",
                "RedacteurAgent", "ProductionAgent", "TesteurAgent", "ValidationAgent"
            ],
            selected: null
        },

        // États des modales
        modals: {
            addAgent: {
                show: false,
                selectedTeam: null
            }
        },

        // États des erreurs
        errors: {
            messages: new Map(),
            retryAttempts: new Map(),
            maxRetries: 3,
            retryDelay: 1000,
            current: null,
            show: false
        },

        // États de monitoring
        monitoring: {
            pollInterval: 30000,
            statsInterval: null,
            healthChecks: new Map(),
            lastUpdates: new Map(),
            errors: new Map(),
            retryAttempts: new Map(),
            maxRetries: 3,
            backoffDelay: 1000
        },

        statusCache: {
            data: new Map(),
            ttl: 5000,
            lastCleanup: Date.now()
        }
    }
}
