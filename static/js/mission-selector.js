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
            missionService: new MissionService(),
            hoveredMissionId: null,
            errorMessage: null,
            showError: false,
            runningStates: new Map(),
            stateUpdateQueue: [], // Queue for state updates
            stateUpdateInProgress: false,
            connectionCheckInProgress: false,
            serverRetries: 0,
            maxRetries: 3,
            retryDelay: 1000,
            serverCheckInterval: null,
            connectionStatus: {
                connected: true,
                lastCheck: null,
                retryCount: 0
            }
        }
    },
    computed: {
        sortedMissions() {
            return [...this.localMissions].sort((a, b) => {
                const dateA = new Date(a.updated_at || a.created_at);
                const dateB = new Date(b.updated_at || b.created_at);
                return dateB - dateA;
            });
        },
        missionStates() {
            return this.missions.reduce((acc, mission) => {
                acc[mission.id] = {
                    running: this.runningStates.get(mission.id) || false,
                    loading: false
                };
                return acc;
            }, {});
        }
    },
    async mounted() {
        console.log('MissionSelector mounted');
        try {
            await this.checkConnection();
            this.startConnectionMonitoring();

            await this.retryWithBackoff(async () => {
                const [agentsResponse, missionsResponse] = await Promise.all([
                    fetch('/api/agents/list'),
                    fetch('/api/missions')
                ]);

                if (!agentsResponse.ok) {
                    throw new Error(`Failed to fetch agents: ${agentsResponse.statusText}`);
                }
                if (!missionsResponse.ok) {
                    throw new Error(`Failed to fetch missions: ${missionsResponse.statusText}`);
                }

                const agents = await agentsResponse.json();
                const missions = await missionsResponse.json();

                this.localMissions = missions;
                this.$emit('update:missions', missions);

                missions.forEach(mission => {
                    this.runningStates.set(mission.id, false);
                });
            });

        } catch (error) {
            console.error('Error in MissionSelector mounted:', error);
            this.handleError({
                title: 'Initialization Error',
                message: error.message,
                type: 'error'
            });
        }
    },
    watch: {
        missions: {
            handler(newMissions) {
                this.localMissions = newMissions;
                if (newMissions) {
                    newMissions.forEach(mission => {
                        if (!this.runningStates.has(mission.id)) {
                            this.runningStates.set(missionData.id, false);
                        }
                    });
                }
            },
            immediate: true,
            deep: true
        }
    },

    created() {
        // Initialize running states for existing missions
        if (this.missions) {
            this.missions.forEach(mission => {
                this.runningStates.set(mission.id, false);
            });
        }
    },
    methods: {
        async handleMissionOperation(operation, errorMessage) {
            try {
                return await this.retryWithBackoff(operation);
            } catch (error) {
                // Check if it's a connection error
                if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                    this.connectionStatus.connected = false;
                    throw new Error('Server connection lost. Please check your connection and try again.');
                }
                throw error;
            }
        },

        async retryWithBackoff(operation, maxRetries = 3) {
            let delay = 1000; // Start with 1s delay
            
            for (let i = 0; i < maxRetries; i++) {
                try {
                    return await operation();
                } catch (error) {
                    if (i === maxRetries - 1) throw error;
                    
                    console.warn(`Attempt ${i + 1} failed, retrying in ${delay}ms...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                    delay *= 2; // Exponential backoff
                }
            }
        },

        startConnectionMonitoring() {
            this.checkConnection();
            this.connectionInterval = setInterval(() => {
                this.checkConnection();
            }, 30000); // Check every 30 seconds
        },

        stopConnectionMonitoring() {
            if (this.connectionInterval) {
                clearInterval(this.connectionInterval);
                this.connectionInterval = null;
            }
        },

        async updateRunningState(missionId, state) {
            try {
                if (!missionId) return;
            
                this.stateUpdateQueue.push({ missionId, state });
                if (!this.stateUpdateInProgress) {
                    await this.processStateUpdates();
                }
            } catch (error) {
                console.error('Error updating running state:', error);
                this.handleError('Failed to update mission state');
            }
        },

        async processStateUpdates() {
            if (this.stateUpdateQueue.length === 0) {
                this.stateUpdateInProgress = false;
                return;
            }

            this.stateUpdateInProgress = true;
            try {
                const update = this.stateUpdateQueue.shift();
                this.runningStates.set(update.missionId, update.state);
                await this.processStateUpdates();
            } catch (error) {
                console.error('Error processing state updates:', error);
            } finally {
                this.stateUpdateInProgress = false;
            }
        },

        isRunning(missionId) {
            try {
                return this.runningStates.get(missionId) || false;
            } catch (error) {
                console.error('Error checking running state:', error);
                return false;
            }
        },

        async checkConnection() {
            if (this.connectionCheckInProgress) return;
        
            try {
                this.connectionCheckInProgress = true;
                const isConnected = await this.missionService.apiClient.checkServerConnection();
            
                if (this.connectionStatus.connected !== isConnected) {
                    this.connectionStatus.connected = isConnected;
                    this.connectionStatus.lastCheck = new Date();
                
                    if (isConnected && this.connectionStatus.retryCount > 0) {
                        this.handleError({
                            title: 'Connection Restored',
                            message: 'Server connection has been restored',
                            type: 'success'
                        });
                        this.connectionStatus.retryCount = 0;
                    }
                }
            } catch (error) {
                this.connectionStatus.connected = false;
                this.connectionStatus.retryCount++;
                this.handleConnectionError(error);
            } finally {
                this.connectionCheckInProgress = false;
            }
        },

        handleConnectionError(error) {
            const retryCount = this.connectionStatus.retryCount;
            const message = retryCount > 1 
                ? `Connection lost. Retry attempt ${retryCount}...`
                : 'Connection lost. Retrying...';
            
            this.handleError({
                title: 'Connection Error',
                message: message,
                type: 'connection',
                retry: true,
                details: error.message
            });

            const delay = Math.min(1000 * Math.pow(2, retryCount - 1), 30000);
            setTimeout(() => this.checkConnection(), delay);
        },

        validateMissionState(mission) {
            if (!mission) return false;
            if (!mission.id) return false;
            if (!mission.name) return false;
        
            const requiredProps = ['id', 'name', 'path', 'status'];
            return requiredProps.every(prop => mission.hasOwnProperty(prop));
        },

        async cleanupMissionState() {
            try {
                this.stateUpdateQueue = [];
                this.stateUpdateInProgress = false;
                this.runningStates.clear();
                this.errorMessage = null;
                this.showError = false;
                this.$emit('update:loading', false);
            } catch (error) {
                console.error('Error cleaning up mission state:', error);
            }
        },

        async handleMissionOperation(operation, errorMessage) {
            try {
                return await this.retryWithBackoff(operation);
            } catch (error) {
                // Check if it's a connection error
                if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                    this.serverStatus.connected = false;
                    throw new Error('Server connection lost. Please check your connection and try again.');
                }
                throw error;
            }
        },

        startServerMonitoring() {
            // Check immediately
            this.checkServerStatus();
            // Then check every 30 seconds
            this.serverStatus.checkInterval = setInterval(() => {
                this.checkServerStatus();
            }, 30000);
        },

        stopServerMonitoring() {
            if (this.serverStatus.checkInterval) {
                clearInterval(this.serverStatus.checkInterval);
                this.serverStatus.checkInterval = null;
            }
        },

        async checkServerStatus() {
            try {
                const isConnected = await this.checkServerConnection();
                this.serverStatus.connected = isConnected;
                this.serverStatus.lastCheck = new Date();
            } catch (error) {
                this.serverStatus.connected = false;
                this.serverStatus.lastCheck = new Date();
                console.warn('Server connection check failed:', error);
            }
        },

        handleError(error) {
            const message = typeof error === 'string' ? error : (
                error.message || 'An unexpected error occurred'
            );
            this.errorMessage = message;
            this.showError = true;
            setTimeout(() => {
                this.showError = false;
            }, 5000);
        },

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

        async retryWithBackoff(operation) {
            let delay = this.retryDelay;
            
            for (let i = 0; i < this.maxRetries; i++) {
                try {
                    return await operation();
                } catch (error) {
                    if (i === this.maxRetries - 1) throw error;
                    
                    console.warn(`Attempt ${i + 1} failed, retrying in ${delay}ms...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                    delay *= 2; // Exponential backoff
                }
            }
        },

        async selectMission(missionData) {
            if (!missionData?.id) {
                this.handleError('Invalid mission selected');
                return;
            }

            try {
                this.$emit('update:loading', true);

                // Check server status first
                if (!this.connectionStatus.connected) {
                    await this.checkConnection();
                    if (!this.connectionStatus.connected) {
                        throw new Error('Server is not available. Please try again later.');
                    }
                }

                const wasRunning = this.runningStates.get(mission.id) || false;

                // Stop agents if running
                if (wasRunning) {
                    try {
                        await this.retryWithBackoff(async () => {
                            const response = await fetch('/api/agents/stop', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                signal: AbortSignal.timeout(5000)
                            });
                            
                            if (!response.ok) throw new Error('Failed to stop agents');
                            this.runningStates.set(mission.id, false);
                        });
                    } catch (stopError) {
                        console.warn('Warning: Failed to stop agents', stopError);
                        this.handleError('Warning: Failed to stop agents, but continuing mission selection');
                    }
                }

                // Select mission with retries
                const result = await this.retryWithBackoff(async () => {
                    const response = await fetch(`/api/missions/${missionData.id}/select`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        signal: AbortSignal.timeout(5000)
                    });

                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.error || 'Failed to select mission');
                    }

                    return response.json();
                });

                // Update state
                this.$emit('select-mission', result);
                this.$emit('update:current-mission', result);

                // Restore previous state if needed
                if (wasRunning) {
                    try {
                        await this.retryWithBackoff(async () => {
                            const response = await fetch('/api/agents/start', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                signal: AbortSignal.timeout(5000)
                            });
                            
                            if (!response.ok) throw new Error('Failed to restart agents');
                            this.runningStates.set(missionData.id, true);
                        });
                    } catch (startError) {
                        console.warn('Warning: Failed to restart agents', startError);
                        this.handleError('Warning: Failed to restart agents after mission selection');
                    }
                }

                return result;

            } catch (error) {
                console.error('Mission selection failed:', error);
                this.runningStates.set(mission.id, false);
                this.handleError(
                    `Failed to select mission: ${error.message}. ` +
                    'Please ensure the server is running and try again.'
                );
                throw error;
            } finally {
                this.$emit('update:loading', false);
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
            <!-- Connection status indicator -->
            <div v-if="!connectionStatus.connected" 
                 class="connection-error bg-red-100 border-l-4 border-red-500 p-4 mb-4">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <i class="mdi mdi-alert-circle text-red-500"></i>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm text-red-700">
                            Server connection lost. Retrying...
                        </p>
                    </div>
                </div>
            </div>
            
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
                        <div class="mission-content">
                            <div v-if="sidebarCollapsed" class="mission-letter">
                                ${ mission.name.charAt(0).toUpperCase() }
                            </div>
                            <span v-else class="mission-name">${ mission.name }</span>
                        </div>
                            <div v-if="sidebarCollapsed" class="mission-letter">
                                ${ mission.name.charAt(0).toUpperCase() }
                            </div>
                            <span v-else class="mission-name">${ mission.name }</span>
                        </div>
                        <div class="flex items-center">
                            <!-- Date tooltip -->
                            <transition name="fade">
                                <span v-if="hoveredMissionId === mission.id"
                                      class="absolute right-16 bg-gray-800 text-white text-xs px-2 py-1 rounded shadow-lg"
                                      style="top: 50%; transform: translateY(-50%)">
                                    ${ formatDate(mission.updated_at || mission.created_at) }
                                </span>
                            </transition>
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
