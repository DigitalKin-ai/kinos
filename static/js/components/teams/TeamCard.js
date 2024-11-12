import TeamMetrics from './TeamMetrics.js';

export default {
    name: 'TeamCard',
    components: {
        TeamMetrics
    },
    props: {
        team: {
            type: Object,
            required: true,
            validator: function(value) {
                return value && typeof value === 'object' && 
                       'id' in value && 
                       'name' in value && 
                       Array.isArray(value.agents);
            }
        },
        loading: Boolean,
        error: String,
        isActive: Boolean,
        metrics: {
            type: Object,
            default: () => ({
                totalAgents: 0,
                runningAgents: 0,
                healthyAgents: 0,
                efficiency: 0,
                lastUpdate: null
            })
        }
    },
    emits: ['toggle', 'activate', 'add-agent', 'toggle-agent'],
    methods: {
        async handleAgentToggle(agent) {
            try {
                const response = await fetch(`/api/teams/${this.team.id}/agents/${agent}/toggle`, {
                    method: 'POST'
                });
                if (!response.ok) throw new Error('Failed to toggle agent');
                this.$emit('toggle-agent', {
                    teamName: this.team.name,
                    agent: agent
                });
            } catch (error) {
                console.error('Error toggling agent:', error);
                throw error;
            }
        },

        getTeamStatusClass() {
            return {
                'bg-red-500': this.team.running,
                'bg-green-500': !this.team.running,
                'hover:bg-red-600': this.team.running,
                'hover:bg-green-600': !this.team.running,
                'text-white': true,
                'font-medium': true
            };
        }
    },
    template: `
        <div class="bg-white rounded-lg shadow-md p-6 team-card relative">
            <!-- Loading indicator -->
            <div v-if="loading" 
                 class="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
                <i class="mdi mdi-loading mdi-spin text-2xl text-blue-500"></i>
            </div>
            
            <!-- Error message -->
            <div v-if="error"
                 class="bg-red-100 border-l-4 border-red-500 p-4 mb-4">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <i class="mdi mdi-alert text-red-500"></i>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm text-red-700">{{ error }}</p>
                    </div>
                </div>
            </div>

            <div class="flex justify-between items-center mb-4">
                <h3 class="text-xl font-semibold">{{ team.name }}</h3>
                <div class="flex items-center space-x-2">
                    <button @click="$emit('add-agent')"
                            class="p-2 rounded-full hover:bg-gray-100"
                            title="Add agent to team">
                        <i class="mdi mdi-plus text-gray-600"></i>
                    </button>
                    <button @click="$emit('toggle')"
                            :class="[
                                'px-4 py-2 rounded text-white font-medium',
                                team.running ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'
                            ]">
                        {{ team.running ? 'Stop' : 'Start' }}
                    </button>
                    <button @click="$emit('activate')"
                            :class="{'bg-green-500': isActive}"
                            class="px-3 py-1 rounded text-white"
                            :disabled="isActive">
                        {{ isActive ? 'Active' : 'Activate' }}
                    </button>
                </div>
            </div>

            <team-metrics 
                v-if="metrics"
                :team="team"
                :metrics="metrics"
                class="mb-4">
            </team-metrics>

            <agent-list 
                :agents="team.agents"
                :team-name="team.name">
            </agent-list>
        </div>
    `
};
