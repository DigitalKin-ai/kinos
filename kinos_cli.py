import argparse
import sys
from datetime import datetime
from services.team_service import TeamService
from services.mission_service import MissionService
from services.agent_service import AgentService
from utils.logger import Logger

class KinosCLI:
    def __init__(self):
        self.logger = Logger()
        self.mission_service = MissionService()
        
        # Créer explicitement un AgentService
        self.agent_service = AgentService(None)
        
        # Ajouter une méthode log directement à l'instance
        self.log = self.logger.log
        
        # Passer self avec l'agent_service ajouté
        self.team_service = TeamService(self)

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

    def list_agents(self):
        """Liste tous les agents disponibles"""
        try:
            # Récupérer la liste des agents
            agents = self.agent_service.get_available_agents()
            
            if not agents:
                self.logger.log("Aucun agent n'a été trouvé.", 'warning')
                return

            self.logger.log("Agents disponibles :", 'info')
            for agent in agents:
                self.logger.log(f"- {agent}", 'info')

        except Exception as e:
            self.logger.log(f"Erreur lors de la récupération des agents : {e}", 'error')
            sys.exit(1)

    def list_missions(self):
        """Liste toutes les missions disponibles"""
        try:
            missions = self.mission_service.get_all_missions()
            
            if not missions:
                self.logger.log("Aucune mission n'a été trouvée.", 'warning')
                return

            self.logger.log("Missions disponibles :", 'info')
            for mission in missions:
                self.logger.log(
                    f"- ID: {mission['id']}, Nom: {mission['name']}, "
                    f"Statut: {mission['status']}, "
                    f"Créée le: {mission['created_at']}", 
                    'info'
                )

        except Exception as e:
            self.logger.log(f"Erreur lors de la récupération des missions : {e}", 'error')
            sys.exit(1)

    def list_teams(self):
        """Liste toutes les équipes prédéfinies"""
        try:
            # Utiliser TeamService pour obtenir les équipes prédéfinies
            teams = self.team_service.get_predefined_teams()
            
            if not teams:
                self.logger.log("Aucune équipe n'a été trouvée.", 'warning')
                return

            self.logger.log("Équipes disponibles :", 'info')
            for team in teams:
                self.logger.log(
                    f"- ID: {team['id']}, Nom: {team['name']}, "
                    f"Agents: {', '.join(team['agents'])}", 
                    'info'
                )

        except Exception as e:
            self.logger.log(f"Erreur lors de la récupération des équipes : {e}", 'error')
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
    
    # Nouvelle commande list globale
    list_parser = subparsers.add_parser('list', help='Lister tous les éléments')
    
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

    # Sous-commande pour les agents
    agent_parser = subparsers.add_parser('agent', help='Commandes liées aux agents')
    agent_subparsers = agent_parser.add_subparsers(dest='agent_command')

    # Commande list pour les agents
    list_parser = agent_subparsers.add_parser('list', help='Lister tous les agents disponibles')

    # Sous-commande pour lister les missions
    missions_parser = subparsers.add_parser('missions', help='Commandes liées aux missions')
    missions_subparsers = missions_parser.add_subparsers(dest='missions_command')
    missions_list_parser = missions_subparsers.add_parser('list', help='Lister toutes les missions')

    # Sous-commande pour lister les équipes
    teams_parser = subparsers.add_parser('teams', help='Commandes liées aux équipes')
    teams_subparsers = teams_parser.add_subparsers(dest='teams_command')
    teams_list_parser = teams_subparsers.add_parser('list', help='Lister toutes les équipes')

    args = parser.parse_args()

    cli = KinosCLI()

    # Dispatch des commandes
    if args.command == 'list':
        # Lister tous les éléments
        cli.list_agents()
        cli.list_missions()
        cli.list_teams()
    elif args.command == 'team' and args.team_command == 'launch':
        cli.launch_team(
            mission_name=args.mission, 
            team_name=args.team, 
            verbose=args.verbose,
            dry_run=args.dry_run,
            timeout=args.timeout,
            log_file=args.log_file
        )
    elif args.command == 'agent' and args.agent_command == 'list':
        cli.list_agents()
    elif args.command == 'missions' and args.missions_command == 'list':
        cli.list_missions()
    elif args.command == 'teams' and args.teams_command == 'list':
        cli.list_teams()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
import argparse
import sys
import logging
from services.team_service import TeamService
from config.global_config import GlobalConfig  # Assurez-vous que cette importation est correcte

def load_default_config():
    """Charger une configuration par défaut si aucune méthode de chargement n'est disponible"""
    return {
        'anthropic_api_key': None,
        'openai_api_key': None,
        'paths': {
            'logs_dir': './logs',
            'missions_dir': './missions',
            'prompts_dir': './prompts'
        },
        'log_level': 'INFO'
    }

def setup_logging(config):
    """
    Configurer le système de logging
    
    Args:
        config (dict): Configuration globale
    """
    log_level = config.get('log_level', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config['paths']['logs_dir'] + '/kinos_cli.log')
        ]
    )

def launch_team(args):
    """
    Lancer une équipe pour une mission spécifique
    
    Args:
        args (Namespace): Arguments de ligne de commande
    """
    try:
        # Essayez de charger la configuration, sinon utilisez une configuration par défaut
        config = GlobalConfig.load_config(args.config) if hasattr(GlobalConfig, 'load_config') else load_default_config()
    except Exception:
        config = load_default_config()

    setup_logging(config)
    
    logger = logging.getLogger('kinos_cli.launch_team')
    
    try:
        team_service = TeamService(config)
        
        # Validation des arguments
        if not args.mission:
            logger.error("Nom de mission requis")
            sys.exit(1)
        
        if not args.team:
            logger.error("Nom d'équipe requis")
            sys.exit(1)
        
        # Lancement de l'équipe
        logger.info(f"Lancement de l'équipe {args.team} pour la mission {args.mission}")
        
        # Simulation ou exécution réelle
        if args.dry_run:
            logger.info("Mode dry-run : simulation sans exécution")
            return
        
        # Lancement de l'équipe avec gestion des erreurs
        result = team_service.launch_team(args.mission, args.team, verbose=args.verbose)
        
        if result:
            logger.info(f"Équipe {args.team} lancée avec succès")
        else:
            logger.error(f"Échec du lancement de l'équipe {args.team}")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Erreur lors du lancement de l'équipe : {e}")
        if args.verbose:
            logger.exception("Trace complète de l'erreur")
        sys.exit(1)

def main():
    """
    Point d'entrée principal du CLI KinOS
    """
    # Essayez de charger la configuration, sinon utilisez une configuration par défaut
    try:
        config = GlobalConfig.load_config() if hasattr(GlobalConfig, 'load_config') else load_default_config()
    except Exception:
        config = load_default_config()

    # Parser pour les arguments de ligne de commande
    parser = argparse.ArgumentParser(description="KinOS CLI Tool")
    parser.add_argument('--version', action='version', version='KinOS CLI v0.1.0')
    parser.add_argument('--config', type=str, help='Chemin vers un fichier de configuration personnalisé')
    
    # Sous-commandes
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')
    
    # Sous-commande pour lancer une équipe
    team_parser = subparsers.add_parser('team', help='Commandes liées aux équipes')
    team_parser.add_argument('action', choices=['launch'], help='Action à effectuer')
    team_parser.add_argument('--mission', type=str, help='Nom de la mission')
    team_parser.add_argument('--team', type=str, help='Nom de l\'équipe')
    team_parser.add_argument('--verbose', action='store_true', help='Mode verbose avec logs détaillés')
    team_parser.add_argument('--dry-run', action='store_true', help='Simulation sans exécution')
    team_parser.add_argument('--timeout', type=int, default=3600, help='Timeout en secondes')
    team_parser.add_argument('--log-file', type=str, help='Chemin du fichier de log')
    
    # Parse les arguments
    args = parser.parse_args()
    
    # Dispatch des commandes
    if args.command == 'team' and args.action == 'launch':
        launch_team(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
