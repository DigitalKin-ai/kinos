import ApiClient from './api-client.js';

export default {
    name: 'AgentManager',
    delimiters: ['[[', ']]'],
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
            loading: true,
            error: null
        }
    },
    watch: {
        currentMission: {
            immediate: true,
            handler(newMission) {
                if (newMission) {
                    this.loadAgents();
                }
            }
        }
    },
    methods: {
        async loadAgents() {
            try {
                this.loading = true;
                const response = await fetch('/api/agents/status');
                const status = await response.json();
                this.agentStates = status;
                this.agents = Object.keys(status).map(name => ({
                    id: name,
                    name: name.charAt(0).toUpperCase() + name.slice(1),
                    running: status[name].running
                }));
            } catch (error) {
                console.error('Failed to load agents:', error);
            } finally {
                this.loading = false;
            }
        },

        async toggleAgent(agent) {
            try {
                const action = agent.running ? 'stop' : 'start';
                const response = await fetch(`/api/agent/${agent.id}/${action}`, {
                    method: 'POST'
                });
                const result = await response.json();
                if (result.status === 'success') {
                    agent.running = !agent.running;
                }
            } catch (error) {
                console.error(`Failed to ${action} agent:`, error);
            }
        },

        async loadPrompt(agentId) {
            try {
                const response = await fetch(`/api/agent/${agentId}/prompt`);
                const data = await response.json();
                this.prompts[agentId] = data.prompt;
                this.editingPrompt = agentId;
            } catch (error) {
                console.error('Failed to load prompt:', error);
            }
        },

        async savePrompt(agentId) {
            try {
                const response = await fetch(`/api/agent/${agentId}/prompt`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        prompt: this.prompts[agentId]
                    })
                });
                if (response.ok) {
                    this.editingPrompt = null;
                }
            } catch (error) {
                console.error('Failed to save prompt:', error);
            }
        }
    },
    template: `
        <div class="p-6 h-full overflow-hidden flex flex-col">
            <h2 class="text-2xl font-bold mb-6">Agents Manager</h2>
            
            <div v-if="loading" class="text-gray-600">
                Loading agents...
            </div>
            
            <div v-else class="flex-1 overflow-y-auto">
                <div class="grid grid-cols-1 gap-6">
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
                            <button v-if="editingPrompt !== agent.id" 
                                    @click="loadPrompt(agent.id)"
                                    class="text-blue-500 hover:text-blue-600">
                                Edit
                            </button>
                            <button v-else 
                                    @click="savePrompt(agent.id)"
                                    class="text-green-500 hover:text-green-600">
                                Save
                            </button>
                        </div>
                        <textarea v-if="editingPrompt === agent.id"
                                v-model="prompts[agent.id]"
                                class="w-full h-32 p-2 border rounded"
                                :disabled="agent.running">
                        </textarea>
                        <div v-else class="text-gray-600">
                            Click Edit to modify prompt
                        </div>
                    </div>
                    
                    <div class="text-sm text-gray-500">
                        Last run: [[ agentStates[agent.id]?.last_run || 'Never' ]]
                    </div>
                </div>
                </div>
            </div>
        </div>
    `
};
