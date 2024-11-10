export default {
    name: 'AddAgentModal',
    props: {
        show: Boolean,
        team: Object,
        availableAgents: Array
    },
    emits: ['close', 'add'],
    data() {
        return {
            selectedAgent: null
        }
    },
    template: `
        <div v-if="show" 
             class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 w-96 max-w-lg">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold">Add Agent to {{ team?.name }}</h3>
                    <button @click="$emit('close')" class="text-gray-500 hover:text-gray-700">
                        <i class="mdi mdi-close"></i>
                    </button>
                </div>
                
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Select Agent
                    </label>
                    <select v-model="selectedAgent"
                            class="w-full border rounded-md p-2">
                        <option value="">Choose an agent...</option>
                        <option v-for="agent in availableAgents"
                                :key="agent"
                                :value="agent">
                            {{ agent }}
                        </option>
                    </select>
                </div>
                
                <div class="flex justify-end space-x-2">
                    <button @click="$emit('close')"
                            class="px-4 py-2 border rounded-md text-gray-600 hover:bg-gray-50">
                        Cancel
                    </button>
                    <button @click="$emit('add', selectedAgent)"
                            :disabled="!selectedAgent"
                            class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50">
                        Add to Team
                    </button>
                </div>
            </div>
        </div>
    `
};
