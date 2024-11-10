import MissionSelector from './mission-selector.js';
import TeamsManager from './teams-manager.js';

export default {
    name: 'TeamsApp',
    components: {
        MissionSelector,
        TeamsManager
    },
    data() {
        return {
            currentMission: null,
            missions: [],
            loading: false
        }
    },
    template: `
        <div class="flex h-screen">
            <mission-selector
                :current-mission="currentMission"
                :missions="missions"
                :loading="loading"
                @select-mission="handleMissionSelect"
                @sidebar-toggle="handleSidebarToggle">
            </mission-selector>
            
            <teams-manager
                :current-mission="currentMission"
                class="flex-1">
            </teams-manager>
        </div>
    `,
    methods: {
        async handleMissionSelect(mission) {
            this.currentMission = mission;
        },
        handleSidebarToggle(collapsed) {
            // Handle sidebar collapse if needed
        }
    }
};

// Mount the app
const app = Vue.createApp(TeamsApp);
app.mount('#app');
