export default {
    name: 'ExplorerApp',
    data() {
        return {
            currentMission: null,
            missions: [],
            loading: true,
            files: [],
            searchQuery: '',
            missionSidebarCollapsed: false,
            highlightedFiles: new Set(),
            fileModifications: new Map(),
            fileCheckInterval: null
        }
    },
    methods: {
        fileExists(file) {
            return file && file.size > 0;
        },
        

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
                console.log('Checking files for mission:', this.currentMission.id);
                const response = await fetch(`/api/missions/${this.currentMission.id}/files`);
                if (!response.ok) {
                    console.warn('File check response not OK:', response.status);
                    return;
                }
                
                const currentFiles = await response.json();
                console.log('Current files:', currentFiles);
                
                currentFiles.forEach(file => {
                    const previousModified = this.fileModifications.get(file.path);
                    console.log('File:', file.path, 'Previous:', previousModified, 'Current:', file.modified);
                    if (previousModified && previousModified < file.modified) {
                        console.log('File modified:', file.path);
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
                const response = await fetch(`/api/missions/${missionId}/files?include_content=true`);
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
}
    computed: {
        filteredFiles() {
            if (!this.searchQuery) {
                // Only return files that exist
                return this.files.filter(file => this.fileExists(file));
            }
            const query = this.searchQuery.toLowerCase();
            return this.files.filter(file => 
                this.fileExists(file) && (
                    file.name.toLowerCase().includes(query) ||
                    file.relativePath.toLowerCase().includes(query)
                )
            );
        }
    },


        async checkFileModifications() {
            try {
                if (!this.currentMission?.id) return;

                const response = await fetch(`/api/missions/${this.currentMission.id}/files`);
                if (!response.ok) throw new Error('Failed to fetch files');
                
                const currentFiles = await response.json();
                
                // Only process files that exist
                currentFiles.filter(file => file.size > 0).forEach(file => {
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

        fileExists(file) {
            return file && file.size > 0;
        },

        highlightFile(filePath) {
            this.highlightedFiles.add(filePath);
            setTimeout(() => {
                this.highlightedFiles.delete(filePath);
            }, 2000);
        },

        handleSidebarCollapse(collapsed) {
            this.missionSidebarCollapsed = collapsed;
        },

        async loadMissionFiles() {
            try {
                if (!this.currentMission?.id) return;
                
                // Get mission path first
                const pathData = await this.getMissionPath(this.currentMission.id);
                const missionPath = pathData.path;
                
                const response = await fetch(`/api/missions/${this.currentMission.id}/files`);
                if (!response.ok) throw new Error('Failed to fetch files');
                
                const currentFiles = await response.json();
                
                // Filter to only show files that physically exist
                this.files = currentFiles.filter(file => {
                    try {
                        return file.size > 0; // A file with size > 0 exists
                    } catch {
                        return false;
                    }
                }).map(file => ({
                    ...file,
                    displayPath: file.relativePath || file.path
                }));
            } catch (error) {
                console.error('Error loading files:', error);
            }
        },

        async checkFileModifications() {
            try {
                if (!this.currentMission?.id) return;

                const response = await fetch(`/api/missions/${this.currentMission.id}/files`);
                if (!response.ok) throw new Error('Failed to fetch files');
                
                const currentFiles = await response.json();
                this.files = currentFiles.map(file => ({
                    ...file,
                    displayPath: file.relativePath || file.path
                }));

            } catch (error) {
                console.error('Error checking files:', error);
            }
        },

        getFileSize(file) {
            if (!file.content) return '0';
            return file.content.length.toString();
        },

        async getFileContent(file) {
            try {
                const response = await fetch(
                    `/api/missions/${this.currentMission.id}/files/${encodeURIComponent(file.relativePath || file.path)}`
                );
                
                if (!response.ok) throw new Error('Failed to load file content');
                
                return await response.text();
            } catch (error) {
                console.error('Error loading file content:', error);
                return null;
            }
        },

        selectFile(file) {
            this.highlightedFiles.clear();
            this.highlightedFiles.add(file.path);
        },

        isFileHighlighted(path) {
            return this.highlightedFiles.has(path);
        },

        getFileSize(file) {
            if (!file.content) return '0';
            return file.content.length.toString();
        },

        getFileIcon(file) {
            const ext = file.name.split('.').pop().toLowerCase();
            const icons = {
                'md': 'mdi mdi-language-markdown',
                'txt': 'mdi mdi-file-document-outline',
                'py': 'mdi mdi-language-python',
                'js': 'mdi mdi-language-javascript',
                'json': 'mdi mdi-code-json'
            };
            return icons[ext] || 'mdi mdi-file-outline';
        }
    },
    mounted() {
        this.loadMissions();
        this.startFileWatcher();
    },
    validateTeamState(team) {
        if (!team?.id || !team?.name) {
            console.error('Invalid team state:', team);
            return false;
        }
        if (!Array.isArray(team.agents)) {
            console.error('Team has no agents array:', team);
            return false;
        }
        return true;
    },

    updateTeamState(team, newState) {
        if (!this.validateTeamState(team)) return;
        
        const stats = this.teamStats.get(team.name) || {};
        if (!stats.agentStatus) stats.agentStatus = {};
        
        // Update agent statuses from response
        if (newState.agents) {
            Object.entries(newState.agents).forEach(([agent, status]) => {
                stats.agentStatus[agent] = status.running;
            });
        }
        
        this.teamStats.set(team.name, stats);
        this.updateTeamHistory(team, `Team state updated`);
    },

    clearStaleData() {
        // Clear old team history entries
        for (const [teamName, history] of this.teamHistory.entries()) {
            const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000);
            const filteredHistory = history.filter(entry => entry.timestamp > oneDayAgo);
            this.teamHistory.set(teamName, filteredHistory);
        }
        
        // Clear metrics for inactive teams
        for (const [teamName, stats] of this.teamStats.entries()) {
            if (!this.teams.find(t => t.name === teamName)) {
                this.teamStats.delete(teamName);
            }
        }
    },

    cleanup() {
        this.loadingStates.clear();
        this.errorMessages.clear();
        this.retryAttempts.clear();
        this.stopMetricsPolling();
    },

    beforeUnmount() {
        if (this.fileCheckInterval) {
            clearInterval(this.fileCheckInterval);
        }
        if (this.cleanupInterval) {
            clearInterval(this.cleanupInterval);
        }
        this.cleanup();
        this.stopServerMonitoring();
    }
}
