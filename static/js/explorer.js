import MissionSelector from './mission-selector.js';
import MissionService from './mission-service.js';

const ExplorerApp = {
    components: {
        MissionSelector
    },
    mounted() {
        console.log('ExplorerApp mounted');
        console.log('Missions:', this.missions);
        this.loadMissions();
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
            error: null,
            missionSidebarCollapsed: false,
            fileModifications: new Map(),
            highlightedFiles: new Set(),
            fileCheckInterval: null
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
        startFileWatcher() {
            this.fileCheckInterval = setInterval(() => {
                if (this.currentMission) {
                    this.checkFileModifications();
                }
            }, 1000);
        },

        stopFileWatcher() {
            if (this.fileCheckInterval) {
                clearInterval(this.fileCheckInterval);
                this.fileCheckInterval = null;
            }
        },

        async checkFileModifications() {
            try {
                const response = await fetch(`/api/missions/${this.currentMission.id}/files`);
                if (!response.ok) return;
                
                const currentFiles = await response.json();
                
                currentFiles.forEach(file => {
                    const previousModified = this.fileModifications.get(file.path);
                    if (previousModified && previousModified < file.modified) {
                        this.highlightFile(file.path);
                    }
                    this.fileModifications.set(file.path, file.modified);
                });
            } catch (error) {
                console.error('Error checking file modifications:', error);
            }
        },

        highlightFile(filePath) {
            this.highlightedFiles.add(filePath);
            setTimeout(() => {
                this.highlightedFiles.delete(filePath);
            }, 1000);
        },

        isFileHighlighted(filePath) {
            return this.highlightedFiles.has(filePath);
        },

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

        async selectFile(file) {
            try {
                const response = await fetch(`/api/missions/${this.currentMission.id}/files/${encodeURIComponent(file.relativePath)}`);
                if (!response.ok) {
                    throw new Error('Failed to load file content');
                }
                const content = await response.text();
                // TODO: Implémenter l'affichage du contenu dans une modal ou un panneau
                console.log('File content:', content);
            } catch (error) {
                console.error('Error loading file:', error);
            }
        },

        handleSidebarCollapse(collapsed) {
            this.missionSidebarCollapsed = collapsed;
        }
    },
    mounted() {
        this.loadMissions();
        this.startFileWatcher();
    },

    beforeUnmount() {
        this.stopFileWatcher();
    }
};

export default ExplorerApp;
