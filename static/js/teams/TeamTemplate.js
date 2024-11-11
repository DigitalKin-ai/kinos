export default `
    <div class="p-6 relative h-full flex flex-col">
        <div v-if="showError" 
             class="fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {{ errorMessage }}
        </div>
        
        <div class="mb-6">
            <h2 class="text-2xl font-bold">Teams</h2>
        </div>
        
        <div class="overflow-auto flex-1 pr-2">
            <div v-if="loading" class="flex items-center justify-center h-full">
                <div class="text-center">
                    <i class="mdi mdi-loading mdi-spin text-4xl text-blue-500"></i>
                    <p class="mt-2 text-gray-600">Loading...</p>
                </div>
            </div>

            <div v-else-if="error" class="flex items-center justify-center h-full">
                <div class="text-center text-red-500">
                    <i class="mdi mdi-alert-circle text-4xl"></i>
                    <p class="mt-2">{{ error }}</p>
                </div>
            </div>
            
            <div v-else class="grid grid-cols-1 gap-6">
                <team-card
                    v-for="team in teams"
                    v-if="team && team.id"
                    :key="team.id" 
                    :team="team"
                    :loading="loadingStates.get(team.id)"
                    :error="errorMessages.get(team.id)"
                    :is-active="activeTeam?.name === team.name"
                    @toggle="toggleTeam(team)"
                    @activate="activateTeam(team)"
                    @add-agent="openAddAgentModal(team)">
                </team-card>
            </div>
        </div>

        <add-agent-modal
            :show="showAddAgentModal"
            :team="selectedTeamForEdit"
            :available-agents="getAvailableAgents()"
            @close="closeAddAgentModal"
            @add="addAgentToTeam">
        </add-agent-modal>
    </div>
`
