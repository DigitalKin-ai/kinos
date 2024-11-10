export default {
    name: 'TeamMetrics',
    props: {
        team: {
            type: Object,
            required: true
        },
        metrics: {
            type: Object,
            default: () => ({
                efficiency: 0,
                agentHealth: 0,
                completedTasks: 0,
                averageResponseTime: 0,
                errorRate: 0
            }),
            validator: (value) => {
                const requiredKeys = ['efficiency', 'agentHealth', 'completedTasks', 'averageResponseTime', 'errorRate'];
                return requiredKeys.every(key => key in value);
            }
        }
    },
    computed: {
        efficiency() {
            return Math.round(this.metrics.efficiency * 100);
        },
        healthStatus() {
            const health = this.metrics.agentHealth * 100;
            return {
                class: health > 80 ? 'bg-green-500 text-white' : 
                       health > 50 ? 'bg-yellow-500 text-black' : 
                       'bg-red-500 text-white',
                text: `${Math.round(health)}%`
            };
        },
        errorRateStatus() {
            const errorRate = this.metrics.errorRate * 100;
            return {
                class: errorRate < 10 ? 'text-green-600' : 
                       errorRate < 25 ? 'text-yellow-600' : 
                       'text-red-600',
                text: `${errorRate.toFixed(1)}%`
            };
        }
    },
    methods: {
        formatResponseTime(time) {
            return time < 1000 ? `${time}ms` : `${(time/1000).toFixed(1)}s`;
        }
    },
    template: `
        <div class="bg-white rounded-lg shadow p-4">
            <h3 class="text-lg font-semibold mb-4">Team Performance Metrics</h3>
            
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-gray-50 rounded p-3">
                    <div class="text-sm text-gray-500">Team Efficiency</div>
                    <div class="text-2xl font-bold">{{ efficiency }}%</div>
                    <div class="w-full bg-gray-200 rounded-full h-2.5 mt-2">
                        <div class="bg-blue-600 h-2.5 rounded-full" 
                             :style="{ width: efficiency + '%' }">
                        </div>
                    </div>
                </div>

                <div class="bg-gray-50 rounded p-3">
                    <div class="text-sm text-gray-500">Agent Health</div>
                    <div class="text-2xl font-bold" :class="healthStatus.class">
                        {{ healthStatus.text }}
                    </div>
                </div>

                <div class="bg-gray-50 rounded p-3">
                    <div class="text-sm text-gray-500">Completed Tasks</div>
                    <div class="text-2xl font-bold">
                        {{ metrics.completedTasks }}
                    </div>
                </div>

                <div class="bg-gray-50 rounded p-3">
                    <div class="text-sm text-gray-500">Response Time</div>
                    <div class="text-2xl font-bold">
                        {{ formatResponseTime(metrics.averageResponseTime) }}
                    </div>
                </div>

                <div class="bg-gray-50 rounded p-3 col-span-2">
                    <div class="text-sm text-gray-500">Error Rate</div>
                    <div class="text-2xl font-bold" :class="errorRateStatus.class">
                        {{ errorRateStatus.text }}
                    </div>
                </div>
            </div>
        </div>
    `
};
