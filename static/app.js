const ParallagonApp = {
    data() {
        return {
            running: false,
            content: {
                demande: '',
                specifications: '',
                management: '',
                production: '',
                evaluation: ''
            },
            updateInterval: null
        }
    },
    methods: {
        async startAgents() {
            try {
                await fetch('/api/start', {method: 'POST'});
                this.running = true;
            } catch (error) {
                console.error('Failed to start agents:', error);
            }
        },
        async stopAgents() {
            try {
                await fetch('/api/stop', {method: 'POST'});
                this.running = false;
            } catch (error) {
                console.error('Failed to stop agents:', error);
            }
        },
        async updateContent() {
            try {
                const response = await fetch('/api/content');
                const data = await response.json();
                this.content = data;
            } catch (error) {
                console.error('Failed to update content:', error);
            }
        },
        startUpdateLoop() {
            this.updateInterval = setInterval(this.updateContent, 1000);
        },
        stopUpdateLoop() {
            if (this.updateInterval) {
                clearInterval(this.updateInterval);
            }
        }
    },
    mounted() {
        this.updateContent();
        this.startUpdateLoop();
    },
    beforeUnmount() {
        this.stopUpdateLoop();
    }
};

Vue.createApp(ParallagonApp).mount('#app');
