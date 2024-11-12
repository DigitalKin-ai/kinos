class TeamService:
    """Service for managing teams of agents"""
    
    def __init__(self, web_instance):
        self.web_instance = web_instance
        self.teams = {}
        self.active_team = None
        self.predefined_teams = self._load_predefined_teams()
        self.logger = web_instance.logger if hasattr(web_instance, 'logger') else None

    def _load_predefined_teams(self) -> list:
        """Load predefined team configurations"""
        return [
            {
                'id': 'default',
                'name': "Default Team",
                'agents': [
                    "SpecificationsAgent",
                    "ManagementAgent", 
                    "EvaluationAgent",
                    "ChroniqueurAgent",
                    "DocumentalisteAgent"
                ]
            },
            {
                'id': 'coding',
                'name': "Coding Team", 
                'agents': [
                    "SpecificationsAgent",
                    "ProductionAgent",
                    "TesteurAgent",
                    "DocumentalisteAgent",
                    "ValidationAgent"
                ]
            },
            {
                'id': 'literature-review',
                'name': "Literature Review Team",
                'agents': [
                    "SpecificationsAgent",
                    "EvaluationAgent",
                    "ChroniqueurAgent", 
                    "DocumentalisteAgent",
                    "ValidationAgent"
                ]
            }
        ]

    def start_team(self, team_id: str, base_path: str = None) -> bool:
        """Start a team in the specified directory"""
        try:
            # Validate team exists
            team = next((t for t in self.predefined_teams if t['id'] == team_id), None)
            if not team:
                if self.logger:
                    self.logger.log(f"Team {team_id} not found", 'error')
                return False

            # Initialize and start agents
            if hasattr(self.web_instance, 'agent_service'):
                config = {'mission_dir': base_path} if base_path else {}
                self.web_instance.agent_service.init_agents(config, team['agents'])
                self.web_instance.agent_service.start_all_agents()
                return True
            return False

        except Exception as e:
            if self.logger:
                self.logger.log(f"Error starting team: {str(e)}", 'error')
            return False

    def stop_team(self) -> bool:
        """Stop the currently running team"""
        try:
            if hasattr(self.web_instance, 'agent_service'):
                self.web_instance.agent_service.stop_all_agents()
                return True
            return False
            
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error stopping team: {str(e)}", 'error')
            return False

    def get_predefined_teams(self) -> list:
        """Get list of predefined teams"""
        return self.predefined_teams

    def cleanup(self):
        """Cleanup team resources"""
        try:
            if hasattr(self.web_instance, 'agent_service'):
                self.web_instance.agent_service.stop_all_agents()
            self.teams.clear()
            self.active_team = None
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error in cleanup: {str(e)}", 'error')

    async deactivateTeam(teamId) {
        try {
            const response = await fetch(`/api/teams/${teamId}/deactivate`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Failed to deactivate team');
            
            this.teamStates.set(teamId, { active: false, timestamp: Date.now() });
            if (this.activeTeam?.id === teamId) {
                this.activeTeam = null;
            }
            
            return true;
        } catch (error) {
            console.error('Error deactivating team:', error);
            throw error;
        }
    }

    async getTeamStatus(teamId) {
        try {
            const response = await fetch(`/api/teams/${teamId}/status`);
            if (!response.ok) throw new Error('Failed to fetch team status');
            
            const status = await response.json();
            this.teamStates.set(teamId, {
                ...status,
                timestamp: Date.now()
            });
            
            return status;
        } catch (error) {
            console.error('Error fetching team status:', error);
            throw error;
        }
    }

    async addAgentToTeam(teamId, agentId) {
        try {
            const response = await fetch(`/api/teams/${teamId}/agents`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ agentId })
            });

            if (!response.ok) throw new Error('Failed to add agent to team');
            
            const updatedTeam = await response.json();
            this.teams.set(teamId, updatedTeam);
            
            return updatedTeam;
        } catch (error) {
            console.error('Error adding agent to team:', error);
            throw error;
        }
    }

    async removeAgentFromTeam(teamId, agentId) {
        try {
            const response = await fetch(`/api/teams/${teamId}/agents/${agentId}`, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error('Failed to remove agent from team');
            
            const updatedTeam = await response.json();
            this.teams.set(teamId, updatedTeam);
            
            return updatedTeam;
        } catch (error) {
            console.error('Error removing agent from team:', error);
            throw error;
        }
    }

    getTeamEfficiency(teamId) {
        const team = this.teams.get(teamId);
        if (!team) return 0;

        const status = this.teamStates.get(teamId);
        if (!status) return 0;

        // Calculer l'efficacité basée sur plusieurs métriques
        const metrics = {
            agentHealth: this._calculateAgentHealth(team, status),
            taskCompletion: this._calculateTaskCompletion(status),
            responseTime: this._calculateResponseTime(status),
            errorRate: this._calculateErrorRate(status)
        };

        // Pondération des métriques
        const weights = {
            agentHealth: 0.4,
            taskCompletion: 0.3,
            responseTime: 0.2,
            errorRate: 0.1
        };

        // Calculer le score final
        return Object.entries(metrics).reduce((score, [key, value]) => {
            return score + (value * weights[key]);
        }, 0);
    }

    // Méthodes privées pour le calcul des métriques
    _calculateAgentHealth(team, status) {
        if (!status.agentStatus) return 0;
        const healthyAgents = Object.values(status.agentStatus)
            .filter(agent => agent.health?.is_healthy).length;
        return healthyAgents / team.agents.length;
    }

    _calculateTaskCompletion(status) {
        return status.metrics?.completed_tasks / 100 || 0;
    }

    _calculateResponseTime(status) {
        const avgTime = status.metrics?.average_response_time || 0;
        const maxAcceptableTime = 5000; // 5 secondes
        return Math.max(0, 1 - (avgTime / maxAcceptableTime));
    }

    _calculateErrorRate(status) {
        const errorRate = status.metrics?.error_rate || 0;
        return Math.max(0, 1 - errorRate);
    }
}
