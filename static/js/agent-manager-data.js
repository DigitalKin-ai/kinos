export default {
    data() {
        return {
            teams: [],
            agents: [],
            loading: false,
            error: null,
            activeTeam: null,
            newAgent: { name: '', prompt: '' },
            showCreateModal: false,
            creatingAgent: false,
            showEditModal: false,
            currentEditAgent: null,
            editLoading: false,
            showError: false,
            errorMessage: '',
            prompts: {},
            agentStates: {},
            editingPrompt: null
        };
    },
    computed: {
        areAnyAgentsRunning() {
            return this.agents.some(agent => agent.running);
        }
    }
};
