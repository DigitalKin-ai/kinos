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
        'sidebar-toggle'
    ],
    delimiters: ['${', '}'],
    data() {
        return {
            isCreatingMission: false,
            newMissionName: '',
            sidebarCollapsed: false,
            localMissions: [],
            runningMissions: new Set(),
            missionService: new MissionService()
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

        async selectMission(mission) {
            try {
                this.$emit('update:loading', true);
                
                // Store previous mission state
                const wasRunning = this.runningMissions.has(mission.id);
                
                // Stop agents first
                try {
                    await fetch('/api/agents/stop', { method: 'POST' });
                } catch (stopError) {
                    console.warn('Error stopping agents:', stopError);
                    // Continue with mission selection even if stop fails
                }
                
                // Select new mission
                const response = await fetch(`/api/missions/${mission.id}/select`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `Failed to select mission (${response.status})`);
                }

                const result = await response.json();
                
                // Verify the change was successful with better error handling
                try {
                    const verifyResponse = await fetch(`/api/missions/${mission.id}`);
                    if (!verifyResponse.ok) {
                        if (verifyResponse.status === 404) {
                            throw new Error('Mission not found');
                        } else if (verifyResponse.status === 500) {
                            const errorData = await verifyResponse.json();
                            throw new Error(errorData.error || 'Internal server error during verification');
                        } else {
                            throw new Error(`Verification failed (${verifyResponse.status})`);
                        }
                    }
                    
                    const verifiedMission = await verifyResponse.json();
                    if (!verifiedMission || verifiedMission.id !== mission.id) {
                        throw new Error('Mission verification mismatch');
                    }

                    // Update current mission
                    this.$emit('select-mission', result);
                    this.$emit('update:current-mission', result);
                    
                    // Restore previous running state if needed
                    if (wasRunning) {
                        try {
                            await fetch('/api/agents/start', { method: 'POST' });
                            this.runningMissions.add(mission.id);
                        } catch (startError) {
                            console.warn('Error restarting agents:', startError);
                        }
                    }
                    
                    return result;
                    
                } catch (verifyError) {
                    console.error('Mission verification failed:', verifyError);
                    // Emit error event for parent component
                    this.$emit('error', verifyError.message);
                    throw verifyError;
                }
                
            } catch (error) {
                console.error('Failed to select mission:', error);
                // Clear running state on error
                this.runningMissions.delete(mission.id);
                // Emit error event for parent component
                this.$emit('error', error.message);
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
                <div v-else v-for="mission in localMissions" 
                     :key="mission.id"
                     class="mission-item"
                     :class="{ active: currentMission?.id === mission.id }">
                    <div class="flex items-center justify-between w-full px-4 py-2"
                         @click="selectMission(mission)">
                        <div class="flex items-center">
                            <i class="mdi mdi-folder-outline"></i>
                            <span class="mission-name">\${ mission.name }</span>
                        </div>
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
    `
};
