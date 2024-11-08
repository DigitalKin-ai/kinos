export default {
    name: 'MissionSelector',
    props: {
        currentMission: Object,
        missions: Array,
        loading: Boolean
    },
    mounted() {
        console.log('MissionSelector mounted');
        console.log('Props:', {
            currentMission: this.currentMission,
            missions: this.missions,
            loading: this.loading
        });
    },
    delimiters: ['${', '}'],
    emits: ['select-mission', 'create-mission'],
    data() {
        return {
            isCreatingMission: false,
            newMissionName: '',
            sidebarCollapsed: false
        }
    },
    methods: {
        toggleSidebar() {
            this.sidebarCollapsed = !this.sidebarCollapsed;
            this.$emit('sidebar-toggle', this.sidebarCollapsed);
        },

        startCreatingMission() {
            this.isCreatingMission = true;
            this.$nextTick(() => {
                this.$refs.newMissionInput?.focus();
            });
        },

        cancelCreatingMission() {
            this.isCreatingMission = false;
            this.newMissionName = '';
        },

        async createMission() {
            if (!this.newMissionName.trim()) {
                this.$emit('error', 'Mission name cannot be empty');
                return;
            }
            this.$emit('create-mission', this.newMissionName.trim());
            this.cancelCreatingMission();
        },

        selectMission(mission) {
            this.$emit('select-mission', mission);
        }
    },
    template: `
        <div class="mission-sidebar" :class="{ 'collapsed': sidebarCollapsed }">
            <div class="mission-sidebar-header">
                <h2>Missions</h2>
                <button @click="toggleSidebar" class="mission-collapse-btn">
                    <i class="mdi" :class="sidebarCollapsed ? 'mdi-chevron-right' : 'mdi-chevron-left'"></i>
                </button>
            </div>
            
            <div class="mission-create" v-if="!sidebarCollapsed">
                <div v-if="!isCreatingMission" class="mission-create-actions">
                    <div @click="startCreatingMission" class="mission-create-btn">
                        <i class="mdi mdi-plus"></i>
                        <span>Créer une mission</span>
                    </div>
                </div>
                <div v-else class="mission-create-input-container">
                    <input v-model="newMissionName" 
                           ref="newMissionInput"
                           @keyup.enter="createMission"
                           @blur="cancelCreatingMission"
                           @keyup.esc="cancelCreatingMission"
                           placeholder="Nom de la mission"
                           class="mission-create-input">
                </div>
            </div>
            
            <div class="mission-list" :class="{ 'loading': loading }">
                <div v-if="loading" class="mission-loading">
                    Chargement des missions...
                </div>
                <div v-else-if="missions.length === 0" class="mission-empty">
                    Aucune mission disponible
                </div>
                <div v-else v-for="mission in missions" 
                     :key="mission.id"
                     class="mission-item"
                     :class="{ active: currentMission?.id === mission.id }"
                     @click="selectMission(mission)">
                    <i class="mdi mdi-folder-outline"></i>
                    <span class="mission-name">\${ mission.name }</span>
                </div>
            </div>
        </div>
    `
};
