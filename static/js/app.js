import { createApp } from 'https://unpkg.com/vue@3/dist/vue.esm-browser.js';
import MissionService from './mission-service.js';
import MissionSelector from './mission-selector.js';

// Import debounce utility
const debounce = (fn, delay) => {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn.apply(this, args), delay);
    };
};

const app = createApp({
    components: {
        MissionSelector
    },
    data() {
        return {
            missionService: new MissionService(),
            currentMission: null,
            missions: [],
            loading: true
        }
    },
    async mounted() {
        try {
            // Initialize mission service
            await this.missionService.initialize();
            this.missions = this.missionService.getMissions();
            this.currentMission = this.missionService.getCurrentMission();
            this.loading = false;
        } catch (error) {
            console.error('Failed to initialize missions:', error);
            this.loading = false;
        }
    }
});

app.mount('#app');
