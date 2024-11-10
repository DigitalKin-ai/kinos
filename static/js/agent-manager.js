import ApiClient from './api-client.js';
import TeamMetrics from './teams/TeamMetrics.js';

export default {
    name: 'AgentManager',
    delimiters: ['[[', ']]'],
    components: {
        TeamMetrics
    },
    props: {
        currentMission: Object
    },
    data() {
        return {
            apiClient: new ApiClient(),
            agents: [],
            agentStates: {},
            prompts: {},
            editingPrompt: null,
            loading: false,
            notifications: [],
            stateUpdateQueue: [],
            stateUpdateInProgress: false,
            error: null,
            running: false,
            updateInterval: null,
            content: {},
            previousContent: {},
            isCreatingMission: false,
            newMissionName: '',
            missionSidebarCollapsed: false,
            runningAgents: new Set(),
            activeTab: 'demande',
            content: {
                demande: '',
                specifications: '',
                management: '',
                production: '',
                evaluation: '',
                suivi: ''
            },
            promptChanged: false,
            showPromptModal: false,
            currentPromptAgent: null,
            suiviUpdateInterval: null,
            showCreateModal: false,
            showEditModal: false,
            currentEditAgent: null,
            editLoading: false,
            newAgent: {
                name: '',
                prompt: ''
            },
            creatingAgent: false,
            errorMessage: null,
            showError: false,
            activeTeam: null,
            teams: []
        }
    },
    watch: {
        currentMission: {
            immediate: true,
            async handler(newMission) {
                try {
                    // Validate mission object
                    if (!newMission || !newMission.id) {
                        console.warn('Invalid or empty mission object');
                        this.agents = [];
                        this.teams = [];
                        return;
                    }

                    // Reset loading and error states
                    this.loading = true;
                    this.error = null;

                    // Parallel loading of agents and teams
                    await Promise.all([
                        this.loadAgents(),
                        this.loadTeams()
                    ]);
                } catch (error) {
                    console.error('Error loading mission data:', error);
                    this.error = error.message || 'Failed to load mission data';
                    this.agents = [];
                    this.teams = [];
                } finally {
                    this.loading = false;
                }
            }
        }
    },
    methods: {
        openCreateModal() {
            this.showCreateModal = true;
            this.newAgent = {
                name: '',
                prompt: `# Agent Prompt Template

MISSION:
[Describe the agent's primary mission]

CONTEXT:
[Provide relevant context for the agent]

INSTRUCTIONS:
[List specific instructions for the agent]

RULES:
- [Rule 1]
- [Rule 2]
- [Add more rules as needed]`
            };
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

                // Refresh agents list
                await this.loadAgents();
                
                // Close modal
                this.showCreateModal = false;
                this.newAgent = { name: '', prompt: '' };

            } catch (error) {
                console.error('Failed to create agent:', error);
                this.error = error.message;
            } finally {
                this.creatingAgent = false;
            }
        },

        validateAgentName(name) {
            return /^[a-zA-Z0-9_-]+$/.test(name);
        },

        async startAllAgents() {
            try {
                const response = await fetch('/api/agents/start', {
                    method: 'POST'
                });
                if (response.ok) {
                    // Update state of all agents
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
                    // Update state of all agents
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
                
                // Load agents list from prompt files
                const response = await fetch('/api/agents/list');
                if (!response.ok) {
                    throw new Error('Failed to load agents');
                }
                const agents = await response.json();
                
                // Load agent states
                const statusResponse = await fetch('/api/agents/status');
                const status = await statusResponse.json();
                this.agentStates = status;
                
                // Combine information with additional status fields
                this.agents = agents.map(agent => ({
                    ...agent,
                    running: this.agentStates[agent.id]?.running || false,
                    lastRun: this.agentStates[agent.id]?.last_run || null,
                    status: this.agentStates[agent.id]?.status || 'inactive'
                }));
                
                // Initialize prompts
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
            if (agent.loading) return; // Prevent multiple clicks
            
            try {
                agent.loading = true;
                const action = agent.running ? 'stop' : 'start';
                
                const response = await fetch(`/api/agent/${agent.id}/${action}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

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
            } finally {
                agent.loading = false;
            }
        },

        async loadPrompt(agentId) {
            try {
                // Set loading state for this specific agent
                const agent = this.agents.find(a => a.id === agentId);
                if (agent) {
                    agent.loadingPrompt = true;
                }

                // Add timeout to request
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
                
                // Show edit modal with current prompt
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
                // Clear loading state
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

                // Update stored prompt
                this.prompts[this.currentEditAgent.id] = this.currentEditAgent.prompt;
                
                // Close modal
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
    template: `
        <div class="h-screen flex flex-col">
            <!-- Error notification -->
            <div v-if="showError" 
                 class="fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                {{ errorMessage }}
            </div>

            <!-- Team Metrics -->
            <div v-if="activeTeam" class="mb-6">
                <team-metrics 
                    :team="activeTeam"
                    :metrics="getTeamMetrics(activeTeam.id)">
                </team-metrics>
            </div>
            <div class="sticky top-0 bg-white z-10 p-6 border-b">
                <div class="flex justify-between items-center">
                    <h2 class="text-2xl font-bold">Gestionnaire d'Agents</h2>
                    <div class="flex items-center space-x-4">
                        <button @click="openCreateModal"
                                class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                            <i class="mdi mdi-plus"></i> Nouvel Agent
                        </button>
                    </div>
                </div>
            </div>
            
            <div v-if="loading" class="p-6 text-gray-600">
                Chargement des agents...
            </div>
            
            <div v-else class="flex-1 overflow-y-auto p-6">
                <div class="space-y-6">
                <div v-for="agent in agents" :key="agent.id" 
                     class="bg-white rounded-lg shadow p-6 border border-gray-200">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-xl font-semibold">[[ agent.name ]]</h3>
                        <button @click="toggleAgent(agent)"
                                :class="agent.running ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'"
                                class="px-4 py-2 rounded text-white font-medium">
                            [[ agent.running ? 'Stop' : 'Start' ]]
                        </button>
                    </div>
                    
                    <div class="mb-4">
                        <div class="flex justify-between items-center mb-2">
                            <span class="text-gray-700 font-medium">Prompt</span>
                            <button @click="loadPrompt(agent.id)" 
                                    :disabled="agent.loadingPrompt"
                                    class="text-blue-500 hover:text-blue-600 disabled:opacity-50">
                                <span v-if="agent.loadingPrompt">
                                    <i class="mdi mdi-loading mdi-spin"></i>
                                </span>
                                <span v-else>
                                    <i class="mdi mdi-pencil"></i> Modifier
                                </span>
                            </button>
                        </div>
                        <textarea v-model="prompts[agent.id]"
                                :readonly="editingPrompt !== agent.id"
                                class="w-full h-32 p-2 border rounded"
                                :class="{'bg-gray-50': editingPrompt !== agent.id}"
                                :disabled="agent.running">
                        </textarea>
                    </div>
                    
                    <div class="text-sm text-gray-500">
                        Last run: [[ agentStates[agent.id]?.last_run || 'Never' ]]
                    </div>
                </div>
                </div>
            </div>

            <!-- Create Agent Modal -->
            <div v-if="showCreateModal" 
                 class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div class="bg-white rounded-lg p-6 w-3/4 max-h-[90vh] flex flex-col">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-semibold">Créer un Nouvel Agent</h3>
                        <button @click="closeCreateModal" 
                                class="text-gray-500 hover:text-gray-700">
                            <i class="mdi mdi-close"></i>
                        </button>
                    </div>

                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Nom de l'Agent
                        </label>
                        <input v-model="newAgent.name"
                               class="w-full p-2 border rounded-md"
                               :class="{'border-red-500': newAgent.name && !validateAgentName(newAgent.name)}"
                               placeholder="Entrez le nom de l'agent (lettres, chiffres, underscore, tiret)">
                        <p v-if="newAgent.name && !validateAgentName(newAgent.name)"
                           class="mt-1 text-sm text-red-500">
                            Agent name can only contain letters, numbers, underscore, and hyphen
                        </p>
                    </div>

                    <div class="flex-1 mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Prompt de l'Agent
                        </label>
                        <textarea v-model="newAgent.prompt"
                                  class="w-full h-[400px] p-4 border rounded-md font-mono text-sm"
                                  placeholder="Enter agent prompt">
                        </textarea>
                    </div>

                    <div class="flex justify-end space-x-2">
                        <button @click="closeCreateModal"
                                :disabled="creatingAgent"
                                class="px-4 py-2 border rounded-md text-gray-600 hover:bg-gray-50">
                            Annuler
                        </button>
                        <button @click="createAgent"
                                :disabled="creatingAgent || !newAgent.name || !newAgent.prompt || !validateAgentName(newAgent.name)"
                                class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50">
                            <span v-if="creatingAgent">
                                <i class="mdi mdi-loading mdi-spin mr-1"></i>
                                Creating...
                            </span>
                            <span v-else>Créer l'Agent</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `
};
