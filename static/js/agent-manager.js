import ApiClient from './api-client.js'; 
import AgentManagerData from './agent-manager-data.js';
import AgentManagerMethods from './agent-manager-methods.js';
import AgentManagerTemplate from './agent-manager-template.js';

export default {
    name: 'AgentManager',
    props: {
        currentMission: {
            type: Object,
            validator: (mission) => mission && mission.id !== undefined,
            default: null
        }
    },
    data() {
        return {
            ...AgentManagerData.data(),
            apiClient: new ApiClient(),
            error: null,
            loading: false,
            searchTerm: '',
            newAgent: { name: '', prompt: '' },
            showCreateModal: false,
            creatingAgent: false,
            editingPrompt: null,
            currentEditAgent: null,
            editLoading: false,
            errorMessage: '',
            showError: false,
            agentStates: {},
            agents: [],
            teams: [], // Add teams to data
            prompts: {},
            searchTimeout: null,
            showEditModal: false,
        };
    },
    computed: {
        areAnyAgentsRunning() {
            return this.agents.some(agent => agent.running);
        },
        
        filteredAgents() {
            if (!this.agents) return [];
            return this.agents.filter(agent => 
                this.searchTerm ? 
                agent.name.toLowerCase().includes(this.searchTerm.toLowerCase()) : 
                true
            );
        },
        
        teamAgentCount() {
            return this.teams.reduce((acc, team) => {
                acc[team.id] = team.agents ? team.agents.length : 0;
                return acc;
            }, {});
        }
    },
    watch: {
        currentMission: {
            immediate: true,
            async handler(newMission) {
                if (newMission) {
                    try {
                        this.loading = true;
                        await this.loadTeams();
                        await this.loadAgents();
                    } catch (error) {
                        this.handleError(error);
                    } finally {
                        this.loading = false;
                    }
                }
            }
        }
    },
    methods: {
        ...AgentManagerMethods.methods,
        
        handleError(error) {
            console.error('Agent Manager Error:', error);
            this.error = error.message || 'An unexpected error occurred';
            this.$emit('error', error);
        },
        
        validateAgentName(name) {
            const nameRegex = /^[a-zA-Z][a-zA-Z0-9_-]{2,29}$/;
            return nameRegex.test(name);
        },
        
        validatePrompt(prompt) {
            return prompt && 
                   prompt.trim().length >= 50 && 
                   prompt.includes('MISSION:') && 
                   prompt.includes('INSTRUCTIONS:');
        },
        
        debouncedSearch(searchTerm) {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.searchTerm = searchTerm;
            }, 300);
        },

        closeCreateModal() {
            if (this.newAgent.name || this.newAgent.prompt !== '') {
                if (!confirm('Are you sure you want to close? Any unsaved changes will be lost.')) {
                    return;
                }
            }
            this.showCreateModal = false;
            this.newAgent = { name: '', prompt: '' };
        },

        async createAgent() {
            if (!this.newAgent.name || !this.newAgent.prompt) {
                alert('Both name and prompt are required');
                return;
            }

            try {
                this.creatingAgent = true;
                const response = await fetch('/api/agents', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name: this.newAgent.name,
                        prompt: this.newAgent.prompt
                    })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to create agent');
                }

                await this.loadAgents();
                this.showCreateModal = false;
                this.newAgent = { name: '', prompt: '' };

            } catch (error) {
                console.error('Failed to create agent:', error);
                this.error = error.message;
            } finally {
                this.creatingAgent = false;
            }
        },

        async startAllAgents() {
            try {
                const response = await fetch('/api/agents/start', {
                    method: 'POST'
                });
                if (response.ok) {
                    this.agents.forEach(agent => agent.running = true);
                }
            } catch (error) {
                console.error('Failed to start all agents:', error);
            }
        },

        async stopAllAgents() {
            try {
                const response = await fetch('/api/agents/stop', {
                    method: 'POST'
                });
                if (response.ok) {
                    this.agents.forEach(agent => agent.running = false);
                }
            } catch (error) {
                console.error('Failed to stop all agents:', error);
            }
        },

        areAnyAgentsRunning() {
            return this.agents.some(agent => agent.running);
        },

        async loadAgents() {
            try {
                this.loading = true;
                const response = await fetch('/api/agents/list');
                if (!response.ok) {
                    throw new Error('Failed to load agents');
                }
                const agents = await response.json();
                const statusResponse = await fetch('/api/agents/status');
                const status = await statusResponse.json();
                this.agentStates = status;
                this.agents = agents.map(agent => ({
                    ...agent,
                    running: this.agentStates[agent.id]?.running || false,
                    lastRun: this.agentStates[agent.id]?.last_run || null,
                    status: this.agentStates[agent.id]?.status || 'inactive'
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
                const action = agent.running ? 'stop' : 'start';
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 10000);
                const response = await fetch(`/api/agents/${encodeURIComponent(agent.id)}/${action}`, {
                    method: 'POST',
                    signal: controller.signal,
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `Failed to ${action} agent`);
                }

                const result = await response.json();
                if (result.status === 'success') {
                    agent.running = !agent.running;
                    this.$emit('agent-status-changed', {
                        id: agent.id,
                        running: agent.running
                    });
                }
            } catch (error) {
                console.error('Failed to toggle agent:', error);
                this.error = error.message;
                this.$emit('notification', {
                    type: 'error',
                    message: `Could not ${agent.running ? 'stop' : 'start'} agent: ${error.message}`
                });
            } finally {
                agent.loading = false;
            }
        },

        async loadPrompt(agentId) {
            try {
                const agent = this.agents.find(a => a.id === agentId);
                if (agent) {
                    agent.loadingPrompt = true;
                }

                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000);

                const response = await fetch(`/api/agent/${encodeURIComponent(agentId)}/prompt`, {
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to load prompt');
                }

                const data = await response.json();
                this.prompts[agentId] = data.prompt;
                this.editingPrompt = agentId;
                this.showEditModal = true;
                this.currentEditAgent = {
                    id: agentId,
                    name: agent?.name || agentId,
                    prompt: data.prompt
                };

            } catch (error) {
                console.error('Failed to load prompt:', error);
                this.errorMessage = `Failed to load prompt: ${error.message}`;
                this.showError = true;
                setTimeout(() => this.showError = false, 5000);
            } finally {
                const agent = this.agents.find(a => a.id === agentId);
                if (agent) {
                    agent.loadingPrompt = false;
                }
            }
        },

        closeEditModal() {
            if (this.hasUnsavedChanges()) {
                if (!confirm('You have unsaved changes. Are you sure you want to close?')) {
                    return;
                }
            }
            this.showEditModal = false;
            this.currentEditAgent = null;
            this.editLoading = false;
        },

        hasUnsavedChanges() {
            return this.currentEditAgent && 
                   this.prompts[this.currentEditAgent.id] !== this.currentEditAgent.prompt;
        },

        async saveEditedPrompt() {
            if (!this.currentEditAgent) return;

            try {
                this.editLoading = true;
                const response = await fetch(`/api/agent/${encodeURIComponent(this.currentEditAgent.id)}/prompt`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        prompt: this.currentEditAgent.prompt
                    })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to save prompt');
                }

                this.prompts[this.currentEditAgent.id] = this.currentEditAgent.prompt;
                this.showEditModal = false;
                this.currentEditAgent = null;

            } catch (error) {
                console.error('Failed to save prompt:', error);
                this.errorMessage = `Failed to save prompt: ${error.message}`;
                this.showError = true;
                setTimeout(() => this.showError = false, 5000);
            } finally {
                this.editLoading = false;
            }
        }
    },
    template: AgentManagerTemplate
};
