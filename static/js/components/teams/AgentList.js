export default {
    name: 'AgentList',
    props: {
        agents: {
            type: Array,
            required: true
        },
        teamName: {
            type: String,
            required: true
        }
    },
    emits: ['toggle-agent'],
    methods: {
        getAgentStatusClass(teamName, agent) {
            const isRunning = this.getAgentStatus(teamName, agent);
            return {
                'bg-red-500': isRunning,
                'bg-green-500': !isRunning,
                'hover:bg-red-600': isRunning,
                'hover:bg-green-600': !isRunning,
                'text-white': true,
                'font-medium': true,
                'px-2': true,
                'py-1': true,
                'rounded': true,
                'text-xs': true,
                'transition-colors': true,
                'duration-200': true
            };
        },

        getAgentStatusText(teamName, agent) {
            return this.getAgentStatus(teamName, agent) ? 'Stop' : 'Start';
        },

        getAgentStatus(teamName, agent) {
            // This should be provided by a prop or parent component
            return false; // Default state
        }
    },
    template: `
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <div v-for="agent in agents"
                 :key="agent"
                 class="bg-gray-50 rounded p-3 flex flex-col justify-between">
                <span class="text-sm font-medium mb-2">{{ agent }}</span>
                <button @click="$emit('toggle-agent', agent)"
                        :class="getAgentStatusClass(teamName, agent)"
                        class="w-full">
                    {{ getAgentStatusText(teamName, agent) }}
                </button>
            </div>
        </div>
    `
};
