import TeamMetrics from './TeamMetrics.js';

export default {
    name: 'TeamCard',
    components: {
        TeamMetrics
    },
    props: {
        team: {
            type: Object,
            required: true
        },
        loading: Boolean,
        error: String,
        isActive: Boolean,
        metrics: Object
    },
    emits: ['toggle', 'activate', 'add-agent', 'toggle-agent'],
    methods: {
        handleAgentToggle(agent) {
            this.$emit('toggle-agent', {
                teamName: this.team.name,
                agent: agent
            });
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
