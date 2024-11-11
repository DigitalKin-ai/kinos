import TeamState from './teams/TeamState.js';
import TeamComputed from './teams/TeamComputed.js';
import TeamUtils from './teams/TeamUtils.js';
import TeamMethods from './teams/TeamMethods.js';
import TeamConnectionHandling from './teams/TeamConnectionHandling.js';
import TeamErrorHandling from './teams/TeamErrorHandling.js';
import TeamConstants from './teams/TeamConstants.js';

import TeamCard from './components/teams/TeamCard.js';
import AddAgentModal from './components/teams/AddAgentModal.js';

export default {
    name: 'TeamsManager',
    components: {
        TeamCard,
        AddAgentModal
    },
    props: {
        missionService: {
            type: Object,
            required: true
        },
        currentMission: {
            type: Object,
            default: () => null
        }
    },
    data: TeamState,
    computed: {
        ...TeamComputed
    },
    methods: {
        ...TeamUtils.methods,
        ...TeamMethods.methods,
        ...TeamConnectionHandling.methods,
        ...TeamErrorHandling.methods,
        
        // Uniquement les méthodes spécifiques à ce composant
        getAvailableAgents() {
            if (!this.selectedTeamForEdit) return [];
            return this.availableAgents.filter(agent => 
                !this.selectedTeamForEdit.agents.includes(agent)
            );
        },

        closeAddAgentModal() {
            this.showAddAgentModal = false;
            this.selectedTeamForEdit = null;
            this.selectedAgent = null;
        },

        async addAgentToTeam() {
            if (!this.selectedTeamForEdit || !this.selectedAgent) return;
            try {
                const updatedAgents = [...this.selectedTeamForEdit.agents, this.selectedAgent];
                const teamIndex = this.teams.findIndex(t => t.name === this.selectedTeamForEdit.name);
                if (teamIndex !== -1) {
                    this.teams[teamIndex] = {
                        ...this.teams[teamIndex],
                        agents: updatedAgents
                    };
                }
                this.closeAddAgentModal();
            } catch (error) {
                console.error('Error adding agent to team:', error);
            }
        }
    },
    watch: {
        currentMission: {
            immediate: true,
            async handler(newMission) {
                if (newMission?.id) {
                    try {
                        this.loading = true;
                        await this.loadTeams();
                    } catch (error) {
                        this.handleError('Failed to load teams', error);
                    } finally {
                        this.loading = false;
                    }
                }
            }
        }
    },
    mounted() {
        this.startConnectionMonitoring();
    },
    beforeUnmount() {
        this.stopConnectionMonitoring(); 
    }
}
