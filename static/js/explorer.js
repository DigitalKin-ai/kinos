import MissionSelector from './mission-selector.js';
import MissionService from './mission-service.js';

const ExplorerApp = {
    components: {
        MissionSelector
    },
    delimiters: ['${', '}'],
    setup() {
        const missionService = new MissionService();
        return {
            missionService
        };
    },
    data() {
        return {
            currentMission: null,
            missions: [],
            loading: false,
            files: [],
            searchQuery: '',
            error: null
        };
    },
    computed: {
        filteredFiles() {
            if (!this.searchQuery) return this.files;
            const query = this.searchQuery.toLowerCase();
            return this.files.filter(file => 
                file.name.toLowerCase().includes(query) ||
                file.relativePath.toLowerCase().includes(query)
            );
        }
    },
    methods: {
        async loadMissions() {
            try {
                this.loading = true;
                const missions = await this.missionService.getAllMissions();
                this.missions = missions;
                if (missions.length > 0) {
                    await this.selectMission(missions[0]);
                }
            } catch (error) {
                this.error = error.message;
            } finally {
                this.loading = false;
            }
        },

        async handleMissionSelect(mission) {
            await this.selectMission(mission);
        },

        async selectMission(mission) {
            try {
                this.loading = true;
                this.currentMission = mission;
                await this.loadMissionFiles(mission.id);
            } catch (error) {
                this.error = error.message;
            } finally {
                this.loading = false;
            }
        },

        async loadMissionFiles(missionId) {
            try {
                const response = await fetch(`/api/missions/${missionId}/files`);
                if (!response.ok) {
                    throw new Error('Failed to load mission files');
                }
                this.files = await response.json();
            } catch (error) {
                this.error = error.message;
            }
        },

        getFileIcon(file) {
            const ext = file.name.split('.').pop().toLowerCase();
            const icons = {
                md: 'mdi mdi-markdown',
                txt: 'mdi mdi-file-document-outline',
                py: 'mdi mdi-language-python',
                js: 'mdi mdi-language-javascript',
                json: 'mdi mdi-code-json',
                default: 'mdi mdi-file-outline'
            };
            return icons[ext] || icons.default;
        },

        selectFile(file) {
            // À implémenter : ouverture/prévisualisation du fichier
            console.log('Selected file:', file);
        }
    },
    mounted() {
        this.loadMissions();
    }
};

export default ExplorerApp;
