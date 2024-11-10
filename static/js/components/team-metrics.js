export default {
    name: 'TeamMetrics',
    props: {
        team: {
            type: Object,
            required: true
        },
        metrics: {
            type: Object,
            required: true
        }
    },
    computed: {
        efficiency() {
            return Math.round(this.metrics.efficiency * 100);
        },
        healthStatus() {
            const health = this.metrics.agentHealth * 100;
            return {
                class: health > 80 ? 'bg-green-500' : health > 50 ? 'bg-yellow-500' : 'bg-red-500',
                text: `${Math.round(health)}%`
            };
        }
    },
    template: `
        <div class="bg-white rounded-lg shadow p-4">
            <h3 class="text-lg font-semibold mb-4">Team Metrics</h3>
            
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-gray-50 rounded p-3">
                    <div class="text-sm text-gray-500">Efficiency</div>
                    <div class="text-2xl font-bold">${efficiency}%</div>
                    <div class="w-full bg-gray-200 rounded-full h-2.5">
                        <div class="bg-blue-600 h-2.5 rounded-full" 
                             :style="{ width: efficiency + '%' }">
                        </div>
                    </div>
                </div>

                <div class="bg-gray-50 rounded p-3">
                    <div class="text-sm text-gray-500">Agent Health</div>
                    <div class="text-2xl font-bold" :class="healthStatus.class">
                        ${healthStatus.text}
                    </div>
                </div>

                <div class="bg-gray-50 rounded p-3">
                    <div class="text-sm text-gray-500">Tasks Completed</div>
                    <div class="text-2xl font-bold">
                        ${metrics.completedTasks}
                    </div>
                </div>

                <div class="bg-gray-50 rounded p-3">
                    <div class="text-sm text-gray-500">Response Time</div>
                    <div class="text-2xl font-bold">
                        ${metrics.averageResponseTime}ms
                    </div>
                </div>
            </div>
        </div>
    `
};
