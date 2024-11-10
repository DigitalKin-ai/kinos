import os
import sys
import argparse
from datetime import datetime
from config.cli_config import CLIConfig
from utils.logger import CLILogger
from utils.exceptions import (
    MissionNotFoundError, 
    TeamNotFoundError, 
    TeamActivationError
)
from services.mission_service import MissionService
from services.team_service import TeamService

class KinosCLI:
    def __init__(self):
        self.mission_service = MissionService()
        self.team_service = TeamService(self.mission_service)
        self.config = CLIConfig()

    def launch_team(self, mission_name, team_name, verbose=False, dry_run=False, timeout=None, log_file=None):
        """
        Lance une équipe pour une mission spécifique avec gestion avancée
        """
        # Générer le fichier de log si non spécifié
        if not log_file:
            os.makedirs(self.config.DEFAULT_LOG_DIR, exist_ok=True)
            log_file = os.path.join(
                self.config.DEFAULT_LOG_DIR, 
                self.config.DEFAULT_LOG_FILE.format(timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"))
            )
        
        # Configuration du logger
        logger = CLILogger(verbose=verbose, log_file=log_file)
        
        try:
            # Validation de la mission
            mission = self.mission_service.get_mission_by_name(mission_name)
            if not mission:
                raise MissionNotFoundError(f"Mission '{mission_name}' non trouvée.")
            
            # Validation de l'équipe
            team_details = self.config.get_team_details(team_name)
            if not team_details:
                raise TeamNotFoundError(f"Équipe '{team_name}' non trouvée.")
            
            # Mode simulation
            if dry_run:
                logger.info(f"Mode simulation : Lancement de l'équipe {team_name} pour la mission {mission_name}")
                return
            
            # Lancement de l'équipe avec gestion du timeout
            try:
                result = self._launch_team_with_timeout(
                    mission['id'], 
                    team_name, 
                    timeout or self.config.DEFAULT_TIMEOUT,
                    logger
                )
                
                # Log du résultat
                logger.info(f"✓ Équipe {team_name} lancée avec succès pour la mission {mission_name}")
                
                # Affichage des résultats d'activation des agents
                for agent_result in result.get('activation_results', []):
                    status = agent_result['status']
                    agent = agent_result['agent']
                    if status == 'error':
                        logger.error(f"Erreur pour l'agent {agent}: {agent_result.get('error', 'Erreur inconnue')}")
                    else:
                        logger.info(f"Agent {agent} : {status}")
                
            except Exception as activation_error:
                raise TeamActivationError(f"Échec de l'activation de l'équipe : {str(activation_error)}")
        
        except (MissionNotFoundError, TeamNotFoundError, TeamActivationError) as e:
            logger.error(str(e))
            sys.exit(1)
        except Exception as e:
            logger.error(f"Erreur inattendue : {str(e)}")
            sys.exit(1)

    def _launch_team_with_timeout(self, mission_id, team_name, timeout, logger):
        """
        Lance l'équipe avec gestion du timeout
        """
        import signal
        import threading
        
        # Résultat de l'activation
        activation_result = [None]
        # Exception potentielle
        exception = [None]
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Délai de {timeout} secondes dépassé pour l'activation de l'équipe")
        
        def team_activation_thread():
            try:
                result = self.team_service.activate_team(mission_id, team_name)
                activation_result[0] = result
            except Exception as e:
                exception[0] = e
        
        # Créer et démarrer le thread
        thread = threading.Thread(target=team_activation_thread)
        thread.start()
        
        # Attendre la fin du thread avec timeout
        thread.join(timeout=timeout)
        
        # Vérifier s'il y a eu une exception
        if exception[0]:
            raise exception[0]
        
        # Vérifier si le thread a terminé
        if thread.is_alive():
            raise TimeoutError(f"Délai de {timeout} secondes dépassé pour l'activation de l'équipe")
        
        return activation_result[0]

def main():
    parser = argparse.ArgumentParser(description='KinOS CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commandes CLI')

    # Sous-commande pour lancer une équipe
    team_parser = subparsers.add_parser('team', help='Commandes liées aux équipes')
    team_subparsers = team_parser.add_subparsers(dest='team_command')

    launch_parser = team_subparsers.add_parser('launch', help='Lancer une équipe')
    launch_parser.add_argument('--mission', required=True, help='Nom de la mission')
    launch_parser.add_argument('--team', required=True, help='Nom de l\'équipe')
    launch_parser.add_argument('--verbose', action='store_true', help='Mode débogage détaillé')
    launch_parser.add_argument('--dry-run', action='store_true', help='Simulation sans exécution')
    launch_parser.add_argument('--timeout', type=int, help='Limite de temps en secondes')
    launch_parser.add_argument('--log-file', help='Fichier de log personnalisé')

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
