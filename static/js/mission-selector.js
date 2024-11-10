import MissionService from './mission-service.js';

export default {
    name: 'MissionSelector',
    props: {
        currentMission: {
            type: Object,
            default: () => null
        },
        missions: {
            type: Array,
            default: () => []
        },
        loading: {
            type: Boolean,
            default: false
        }
    },
    emits: [
        'select-mission', 
        'update:loading',
        'update:current-mission',
        'update:missions',
        'create-mission', 
        'sidebar-toggle',
        'error'
    ],
    delimiters: ['${', '}'],
    data() {
        return {
            isCreatingMission: false,
            newMissionName: '',
            sidebarCollapsed: false,
            localMissions: [],
            runningMissions: new Set(),
            missionService: new MissionService(),
            hoveredMissionId: null,
            errorMessage: null,
            showError: false
        }
    },
    computed: {
        sortedMissions() {
            return [...this.localMissions].sort((a, b) => {
                const dateA = new Date(a.updated_at || a.created_at);
                const dateB = new Date(b.updated_at || b.created_at);
                return dateB - dateA;
            });
        }
    },
    async mounted() {
        console.log('MissionSelector mounted');
        try {
            console.log('Initial props:', {
                currentMission: this.currentMission,
                missions: this.missions,
                loading: this.loading
            });

            // Récupérer la liste des agents depuis l'API
            const agentsResponse = await fetch('/api/agents/list');
            if (!agentsResponse.ok) {
                throw new Error(`Failed to fetch agents: ${agentsResponse.statusText}`);
            }
            const agents = await agentsResponse.json();
            
            const response = await fetch('/api/missions');
            if (!response.ok) {
                throw new Error(`Failed to fetch missions: ${response.statusText}`);
            }
            const missions = await response.json();
            console.log('Fetched missions:', missions);
            
            this.localMissions = missions;
            this.$emit('update:missions', missions); // Utiliser l'émission déclarée
        } catch (error) {
            console.error('Error in MissionSelector mounted:', error);
        }
    },
    watch: {
        missions: {
            immediate: true,
            handler(newMissions) {
                this.localMissions = newMissions;
            }
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
            try {
                const newMission = await this.missionService.createMission(this.newMissionName.trim());
                this.missions.push(newMission);
                // Sélectionner automatiquement la nouvelle mission
                this.$emit('select-mission', newMission);
                this.currentMission = newMission;
                this.cancelCreatingMission();
            } catch (error) {
                console.error('Failed to create mission:', error);
                this.$emit('error', error.message);
            }
        },

        async checkServerConnection() {
            try {
                const response = await Promise.race([
                    fetch('/api/status', {
                        method: 'GET',
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json'
                        }
                    }),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Request timeout')), 5000)
                    )
                ]);

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `Server returned ${response.status}`);
                }

                const data = await response.json();
                return data.server?.running === true;
            } catch (error) {
                console.error('Server connection check failed:', error);
                throw error;
            }
        },

        handleError(message) {
            this.errorMessage = message;
            this.showError = true;
            setTimeout(() => {
                this.showError = false;
            }, 5000);
        },

        async selectMission(mission) {
            try {
                this.$emit('update:loading', true);

                // Check server connection first
                const isServerAvailable = await this.checkServerConnection();
                if (!isServerAvailable) {
                    throw new Error('Server is not responding. Please check if the server is running.');
                }

                // Validate mission object
                if (!mission?.id) {
                    throw new Error('Invalid mission data');
                }

                // Store previous mission state
                const wasRunning = this.runningMissions.has(mission.id);
                
                // Stop agents with timeout and error handling
                try {
                    const stopResponse = await Promise.race([
                        fetch('/api/agents/stop', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' }
                        }),
                        new Promise((_, reject) => 
                            setTimeout(() => reject(new Error('Request timeout')), 5000)
                        )
                    ]);

                    if (!stopResponse.ok) {
                        console.warn('Warning: Failed to stop agents cleanly');
                    }
                } catch (stopError) {
                    console.warn('Error stopping agents:', stopError);
                }

                // Select mission with retry logic
                const maxRetries = 3;
                let lastError = null;

                for (let attempt = 0; attempt < maxRetries; attempt++) {
                    try {
                        const response = await Promise.race([
                            fetch(`/api/missions/${mission.id}/select`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' }
                            }),
                            new Promise((_, reject) => 
                                setTimeout(() => reject(new Error('Request timeout')), 5000)
                            )
                        ]);

                        if (!response.ok) {
                            const errorData = await response.json();
                            throw new Error(errorData.error || `Failed to select mission (${response.status})`);
                        }

                        const result = await response.json();
                        
                        // Update mission state
                        this.$emit('select-mission', result);
                        this.$emit('update:current-mission', result);

                        // Restore previous running state if needed
                        if (wasRunning) {
                            try {
                                await fetch('/api/agents/start', { 
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' }
                                });
                                this.runningMissions.add(mission.id);
                            } catch (startError) {
                                console.warn('Error restarting agents:', startError);
                                this.handleError('Warning: Failed to restart agents');
                            }
                        }

                        return result;

                    } catch (error) {
                        lastError = error;
                        if (attempt < maxRetries - 1) {
                            await new Promise(resolve => 
                                setTimeout(resolve, Math.pow(2, attempt + 1) * 1000)
                            );
                            continue;
                        }
                    }
                }

                throw new Error(`Failed to select mission after ${maxRetries} attempts: ${lastError?.message}`);

            } catch (error) {
                console.error('Mission selection failed:', error);
                this.runningMissions.delete(mission?.id);
                this.handleError(error.message);
                throw error;
            } finally {
                this.$emit('update:loading', false);
            }
        },

        async toggleMissionAgents(mission, event) {
            event.stopPropagation();
            try {
                const isRunning = this.runningMissions.has(mission.id);
                const endpoint = isRunning ? '/api/agents/stop' : '/api/agents/start';
                
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ missionId: mission.id })
                });

                if (response.ok) {
                    if (isRunning) {
                        this.runningMissions.delete(mission.id);
                    } else {
                        this.runningMissions.add(mission.id);
                    }
                }
            } catch (error) {
                console.error('Error toggling agents:', error);
            }
        },
        formatDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            const today = new Date();
            const isToday = date.toDateString() === today.toDateString();
            
            const time = date.toLocaleTimeString('fr-FR', {
                hour: '2-digit',
                minute: '2-digit'
            });
            
            if (isToday) {
                return `Today ${time}`;
            }
            
            return `${date.toLocaleDateString('fr-FR')} ${time}`;
        }
    },
    template: `
        <div class="mission-sidebar" :class="{ 'collapsed': sidebarCollapsed }">
            <!-- Error alert -->
            <div v-if="showError" 
                 class="error-alert bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
                <strong class="font-bold">Error!</strong>
                <span class="block sm:inline">\${errorMessage}</span>
                <span class="absolute top-0 bottom-0 right-0 px-4 py-3" @click="showError = false">
                    <svg class="fill-current h-6 w-6 text-red-500" role="button" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                        <title>Close</title>
                        <path d="M14.348 14.849a1.2 1.2 0 0 1-1.697 0L10 11.819l-2.651 3.029a1.2 1.2 0 1 1-1.697-1.697l2.758-3.15-2.759-3.152a1.2 1.2 0 1 1 1.697-1.697L10 8.183l2.651-3.031a1.2 1.2 0 1 1 1.697 1.697l-2.758 3.152 2.758 3.15a1.2 1.2 0 0 1 0 1.698z"/>
                    </svg>
                </span>
            </div>

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
                <div v-else v-for="mission in sortedMissions" 
                     :key="mission.id"
                     class="mission-item relative"
                     :class="{ active: currentMission?.id === mission.id }"
                     @mouseenter="hoveredMissionId = mission.id"
                     @mouseleave="hoveredMissionId = null">
                    <div class="flex items-center justify-between w-full px-4 py-2"
                         @click="selectMission(mission)">
                        <div class="flex items-center">
                            <i class="mdi mdi-folder-outline"></i>
                            <span class="mission-name">\${ mission.name }</span>
                        </div>
                        <div class="flex items-center">
                            <!-- Date tooltip -->
                            <transition name="fade">
                                <span v-if="hoveredMissionId === mission.id"
                                      class="absolute right-16 bg-gray-800 text-white text-xs px-2 py-1 rounded shadow-lg"
                                      style="top: 50%; transform: translateY(-50%)">
                                    \${ formatDate(mission.updated_at || mission.created_at) }
                                </span>
                            </transition>
                            <button @click="toggleMissionAgents(mission, $event)"
                                    class="control-button"
                                    :class="{ 'running': runningMissions.has(mission.id) }"
                                    :title="runningMissions.has(mission.id) ? 'Stop agents' : 'Start agents'">
                                <i class="mdi" :class="runningMissions.has(mission.id) ? 'mdi-stop' : 'mdi-play'"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    style: `
        .fade-enter-active, .fade-leave-active {
            transition: opacity 0.2s ease;
        }
        .fade-enter-from, .fade-leave-to {
            opacity: 0;
        }
        
        .mission-item {
            position: relative;
        }
        
        .mission-item .absolute {
            z-index: 10;
            white-space: nowrap;
        }
    `
};
