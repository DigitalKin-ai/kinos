import argparse
import sys
from datetime import datetime
from services.team_service import TeamService
from services.mission_service import MissionService
from utils.logger import Logger

class KinosCLI:
    def __init__(self):
        self.logger = Logger()
        self.mission_service = MissionService()
        self.team_service = TeamService(self)  # Pass web_instance equivalent

    def launch_team(self, mission_name, team_name, verbose=False, dry_run=False, timeout=None, log_file=None):
        """
        Lance une équipe pour une mission spécifique
        
        Args:
            mission_name (str): Nom de la mission
            team_name (str): Nom de l'équipe
            verbose (bool): Mode débogage détaillé
            dry_run (bool): Simulation sans exécution
            timeout (int): Limite de temps en secondes
            log_file (str): Chemin du fichier de log
        """
        try:
            # Validation des paramètres
            mission = self.mission_service.get_mission_by_name(mission_name)
            if not mission:
                self.logger.log(f"Erreur : Mission '{mission_name}' non trouvée.", 'error')
                sys.exit(1)

            # Vérification de l'équipe
            available_teams = self.team_service._load_predefined_teams()
            if team_name not in [team['id'] for team in available_teams]:
                self.logger.log(f"Erreur : Équipe '{team_name}' non trouvée.", 'error')
                sys.exit(1)

            if dry_run:
                self.logger.log(f"Mode simulation : Lancement de l'équipe {team_name} pour la mission {mission_name}", 'info')
                return

            # Lancement de l'équipe
            result = self.team_service.activate_team(mission['id'], team_name)
            
            # Gestion des logs
            if verbose:
                self._stream_logs(result, log_file)
            
            self.logger.log(f"✓ Équipe {team_name} lancée avec succès pour la mission {mission_name}", 'success')

        except Exception as e:
            self.logger.log(f"Erreur lors du lancement de l'équipe : {e}", 'error')
            sys.exit(1)

    def _stream_logs(self, team_result, log_file=None):
        """
        Affiche les logs de l'équipe en temps réel
        
        Args:
            team_result (dict): Résultat de l'activation de l'équipe
            log_file (str, optional): Chemin du fichier de log
        """
        # Affichage des résultats d'activation
        for agent_result in team_result.get('activation_results', []):
            status = agent_result.get('status', 'unknown')
            agent = agent_result.get('agent', 'Unknown Agent')
            
            if status == 'started':
                self.logger.log(f"Agent {agent} démarré avec succès", 'success')
            elif status == 'failed':
                self.logger.log(f"Échec du démarrage de l'agent {agent}", 'error')
            elif status == 'error':
                error = agent_result.get('error', 'Erreur inconnue')
                self.logger.log(f"Erreur pour l'agent {agent}: {error}", 'error')

def main():
    parser = argparse.ArgumentParser(description="KinOS CLI - Gestion des équipes d'agents")
    
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')
    
    # Sous-commande pour lancer une équipe
    team_parser = subparsers.add_parser('team', help='Commandes liées aux équipes')
    team_subparsers = team_parser.add_subparsers(dest='team_command')
    
    launch_parser = team_subparsers.add_parser('launch', help='Lancer une équipe pour une mission')
    launch_parser.add_argument('--mission', required=True, help='Nom de la mission')
    launch_parser.add_argument('--team', required=True, help='Nom de l\'équipe')
    launch_parser.add_argument('--verbose', action='store_true', help='Mode débogage détaillé')
    launch_parser.add_argument('--dry-run', action='store_true', help='Simulation sans exécution')
    launch_parser.add_argument('--timeout', type=int, help='Limite de temps en secondes')
    launch_parser.add_argument('--log-file', help='Chemin du fichier de log')

    args = parser.parse_args()

    cli = KinosCLI()

    if args.command == 'team' and args.team_command == 'launch':
        cli.launch_team(
            mission_name=args.mission, 
            team_name=args.team, 
            verbose=args.verbose,
            dry_run=args.dry_run,
            timeout=args.timeout,
            log_file=args.log_file
        )
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
