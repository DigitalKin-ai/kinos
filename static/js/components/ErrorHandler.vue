<template>
  <div class="error-handler">
    <div 
      v-if="connectionStatus === 'offline'" 
      class="offline-notification"
    >
      Connexion internet perdue
    </div>
    <div 
      v-if="connectionErrors > 0" 
      class="connection-errors"
    >
      Erreurs de connexion : {{ connectionErrors }}
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      connectionStatus: 'online',
      connectionErrors: 0,
      lastErrorTimestamp: null
    }
  },
  mounted() {
    // Écouteurs d'événements de connexion et d'erreur
    window.addEventListener('connection-status-change', this.handleConnectionStatusChange);
    window.addEventListener('connection-error', this.handleConnectionError);
    window.addEventListener('mission-selected', this.handleMissionSelected);
    window.addEventListener('mission-selection-error', this.handleMissionSelectionError);
  },
  methods: {
    handleConnectionStatusChange(event) {
      this.connectionStatus = event.detail.status;
      
      // Notification visuelle
      if (this.connectionStatus === 'offline') {
        this.$notify({
          title: 'Connexion perdue',
          message: 'Vérifiez votre connexion internet',
          type: 'warning'
        });
      }
    },
    
    handleConnectionError(event) {
      const { error, connectionState } = event.detail;
      
      this.connectionErrors = connectionState.connectionErrors;
      this.lastErrorTimestamp = connectionState.lastCheckTimestamp;
      
      // Stratégie de récupération
      if (this.connectionErrors > 3) {
        this.showReconnectionDialog();
      }
    },
    
    handleMissionSelected(event) {
      const { missionId, missionName } = event.detail;
      
      this.$notify({
        title: 'Mission sélectionnée',
        message: `Mission ${missionName} activée avec succès`,
        type: 'success'
      });
    },
    
    handleMissionSelectionError(event) {
      const { error, missionId } = event.detail;
      
      this.$notify({
        title: 'Erreur de sélection',
        message: `Impossible de sélectionner la mission ${missionId}: ${error}`,
        type: 'error'
      });
    },

    showReconnectionDialog() {
      // Implémentation d'un dialogue de reconnexion
      this.$confirm('Problèmes de connexion persistants', 'Voulez-vous réessayer ?', {
        confirmButtonText: 'Réessayer',
        cancelButtonText: 'Annuler',
        type: 'warning'
      }).then(() => {
        // Logique de tentative de reconnexion
        this.attemptReconnection();
      }).catch(() => {
        // Action si l'utilisateur annule
        this.connectionErrors = 0;
      });
    },

    attemptReconnection() {
      // Logique de reconnexion
      const apiClient = new ApiClient();
      apiClient.checkServerConnection()
        .then(isConnected => {
          if (isConnected) {
            this.$notify({
              title: 'Reconnexion réussie',
              message: 'La connexion a été rétablie',
              type: 'success'
            });
            this.connectionErrors = 0;
          } else {
            this.$notify({
              title: 'Échec de reconnexion',
              message: 'Impossible de rétablir la connexion',
              type: 'error'
            });
          }
        });
    }
  }
}
</script>

<style scoped>
.error-handler {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
}

.offline-notification {
  background-color: #ff4949;
  color: white;
  padding: 10px;
  border-radius: 5px;
  margin-bottom: 10px;
}

.connection-errors {
  background-color: #f56c6c;
  color: white;
  padding: 10px;
  border-radius: 5px;
}
</style>
