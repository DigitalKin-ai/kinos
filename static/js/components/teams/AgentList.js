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
