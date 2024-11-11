export default {
    name: 'ErrorNotification',
    props: {
        message: {
            type: String,
            required: true
        },
        show: {
            type: Boolean,
            default: false
        },
        type: {
            type: String,
            default: 'error',
            validator: value => ['error', 'connection', 'warning'].includes(value)
        }
    },
    emits: ['close', 'retry'],
    data() {
        return {
            retrying: false
        }
    },
    computed: {
        notificationClass() {
            return {
                'bg-red-100 border-red-400 text-red-700': this.type === 'error',
                'bg-yellow-100 border-yellow-400 text-yellow-700': this.type === 'warning',
                'bg-blue-100 border-blue-400 text-blue-700': this.type === 'connection'
            }
        },
        showRetry() {
            return this.type === 'connection' || this.type === 'error'
        }
    },
    methods: {
        async retryOperation() {
            if (this.retrying) return;
            
            try {
                this.retrying = true;
                await this.$emit('retry');
            } catch (error) {
                console.error('Error retrying operation:', error);
            } finally {
                this.retrying = false;
            }
        }
    },
    template: `
        <transition name="fade">
            <div v-if="show" 
                 class="fixed top-4 right-4 border px-4 py-3 rounded relative"
                 :class="notificationClass">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <i :class="{
                            'mdi mdi-alert-circle': type === 'error',
                            'mdi mdi-wifi-off': type === 'connection',
                            'mdi mdi-alert': type === 'warning'
                        }" class="mr-2"></i>
                    </div>
                    <div>
                        <strong class="font-bold mr-2">
                            {{ type === 'connection' ? 'Connection Error' : 'Error!' }}
                        </strong>
                        <span class="block sm:inline">{{ message }}</span>
                    </div>
                </div>
                
                <div v-if="showRetry" class="mt-2 flex justify-end">
                    <button @click="retryOperation"
                            :disabled="retrying"
                            class="text-sm underline hover:no-underline focus:outline-none">
                        {{ retrying ? 'Retrying...' : 'Retry' }}
                    </button>
                </div>

                <button @click="$emit('close')"
                        class="absolute top-0 right-0 p-4">
                    <i class="mdi mdi-close"></i>
                </button>
            </div>
        </transition>
    `
}
