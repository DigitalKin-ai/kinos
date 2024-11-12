import argparse
import os
import sys
import time
import logging
from services.team_service import TeamService
from services.mission_service import MissionService
from services.agent_service import AgentService
from utils.logger import configure_cli_logger
from config.global_config import GlobalConfig

def launch_team(args):
    """
    Launch a team with comprehensive error handling and configuration
    
    Args:
        args: Parsed command-line arguments
    """
    try:
        # Load configuration or use default
        config = GlobalConfig.load_config() if hasattr(GlobalConfig, 'load_config') else {}
        
        # Setup logging
        logger = configure_cli_logger()
        
        # Validate required arguments
        if not args.mission:
            logger.log("Mission name is required", 'error')
            sys.exit(1)
        
        if not args.team:
            logger.log("Team name is required", 'error')
            sys.exit(1)
        
        # Create service instances
        mission_service = MissionService()
        team_service = TeamService(None)
        agent_service = AgentService(None)
        
        # Dry run mode
        if args.dry_run:
            logger.log(f"Dry run: Would launch team {args.team} for mission {args.mission}", 'info')
            return
        
        # Get mission details
        mission = mission_service.get_mission_by_name(args.mission)
        if not mission:
            logger.log(f"Mission {args.mission} not found", 'error')
            sys.exit(1)
        
        # Activate team
        result = team_service.activate_team(mission['id'], args.team)
        
        # Log detailed results
        logger.log(f"Team {args.team} launched successfully", 'success')
        
        # Verbose mode: show detailed agent statuses
        if args.verbose:
            for agent_result in result.get('activation_results', []):
                status = 'Success' if agent_result['success'] else 'Failed'
                logger.log(f"Agent {agent_result['agent']}: {status}", 
                           'success' if agent_result['success'] else 'error')
        
    except Exception as e:
        logger.log(f"Error launching team: {e}", 'error')
        sys.exit(1)

def main():
    """Main entry point for KinOS CLI"""
    parser = argparse.ArgumentParser(description="KinOS CLI - Team Launch")
    parser.add_argument('team', nargs='?', default='default', 
                       help='Team to launch (default: default)')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    try:
        # Configure logging
        logger = configure_cli_logger()
        logger.log(f"Starting KinOS CLI...", 'info')
        logger.log(f"Team: {args.team}", 'info')
        logger.log(f"Working directory: {os.getcwd()}", 'info')

        # Create service instances
        team_service = TeamService(None)
        agent_service = AgentService(None)

        # Launch team in current directory
        result = team_service.start_team(
            team_id=args.team, 
            base_path=os.getcwd()
        )

        if args.verbose:
            logger.log("Team launch details:", 'info')
            for agent_result in result.get('start_results', []):
                status = agent_result.get('status', 'unknown')
                agent = agent_result.get('agent', 'Unknown Agent')
                logger.log(f"Agent {agent}: {status}")

    except Exception as e:
        logger = configure_cli_logger()
        logger.log(f"Error launching team: {str(e)}", 'error')
        sys.exit(1)

if __name__ == '__main__':
    main()

def launch_team(self, team_name: str, base_path: str = None, verbose: bool = False):
    """
    Launch a team in current directory or specified path
    
    Args:
        team_name: Name of the team to launch
        base_path: Optional custom base path (defaults to current directory)
        verbose: Enable verbose logging
    """
    try:
        # Use current directory if no base path specified
        mission_dir = base_path or os.getcwd()
        
        # Validate team exists
        available_teams = self.team_service._load_predefined_teams()
        team_ids = [team['id'] for team in available_teams]
        
        if team_name not in team_ids:
            self.logger.log(f"Équipe '{team_name}' non trouvée.", 'error')
            self.logger.log(f"Équipes disponibles : {', '.join(team_ids)}", 'info')
            sys.exit(1)

        # Launch team in specified/current directory
        result = self.team_service.start_team(
            mission_id=None,  # No longer needed
            team_id=team_name, 
            base_path=mission_dir
        )
        
        self.logger.log(f"✓ Équipe {team_name} démarrée. Démarrage des agents...", 'success')
        self.logger.log(f"Dossier de travail : {mission_dir}", 'info')
        
        if verbose:
            self.logger.log("Appuyez sur CTRL+C pour arrêter les agents", 'info')
        
        # Main log display loop
        try:
            while True:
                # Get status of all agents
                status = self.agent_service.get_agent_status()
                
                # Display status for each agent if verbose
                if verbose:
                    for agent_name, agent_status in status.items():
                        running = agent_status.get('running', False)
                        health = agent_status.get('health', {})
                        last_run = agent_status.get('last_run', 'Jamais')
                        
                        status_str = "🟢 Actif" if running else "🔴 Inactif"
                        health_str = "✅ OK" if health.get('is_healthy', True) else "❌ Dégradé"
                        
                        self.logger.log(
                            f"Agent {agent_name}: {status_str} | Santé: {health_str} | "
                            f"Dernière exécution: {last_run}",
                            'info' if running else 'warning'
                        )
                    
                    # Display separator
                    self.logger.log("-" * 80, 'info')
                
                # Wait before next update
                time.sleep(60)

        except KeyboardInterrupt:
            self.logger.log("\nArrêt demandé. Arrêt des agents...", 'warning')
            self.agent_service.stop_all_agents()
            self.logger.log("Tous les agents ont été arrêtés.", 'success')
            sys.exit(0)

    except Exception as e:
        self.logger.log(f"Erreur lors du lancement de l'équipe : {e}", 'error')
        sys.exit(1)
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

def create_robust_web_instance(config=None):
    """
    Crée une instance web robuste avec des services par défaut
    
    Args:
        config (dict, optional): Configuration à utiliser
    
    Returns:
        SimpleNamespace: Instance web complète
    """
    from services.file_manager import FileManager
    from services.mission_service import MissionService
    from services.agent_service import AgentService
    from services.team_service import TeamService
    from services.dataset_service import DatasetService
    from utils.logger import Logger
    from types import SimpleNamespace

    # Utiliser la configuration par défaut si non fournie
    config = config or load_default_config()

    # Créer un logger
    log_instance = Logger()

    # Créer l'instance web
    web_instance = SimpleNamespace(
        logger=log_instance,
        log_message=lambda message, level='info': log_instance.log(message, level),
        log=lambda message, level='info': log_instance.log(message, level),
        config=config,
        
        # Initialize dataset service first
        dataset_service=DatasetService(None),  # Will be updated with web_instance
        
        # Créer des services
        mission_service=MissionService(),
        agent_service=AgentService(None),
        file_manager=FileManager(None, on_content_changed=None),
        team_service=None,  # Sera initialisé après
        
        # Méthodes de log par défaut
        log_error=lambda message: log_instance.log(message, 'error'),
        log_info=lambda message: log_instance.log(message, 'info')
    )

    # Update dataset_service with web_instance
    web_instance.dataset_service.web_instance = web_instance
    
    # Créer le TeamService avec l'instance web
    web_instance.team_service = TeamService(web_instance)

    return web_instance

def launch_team(args):
    try:
        # Essayez de charger la configuration, sinon utilisez une configuration par défaut
        try:
            current_config = GlobalConfig.load_config() if hasattr(GlobalConfig, 'load_config') else load_default_config()
        except Exception:
            current_config = load_default_config()

        # Créer une instance web robuste
        web_instance = create_robust_web_instance(current_config)
        
        setup_logging(current_config)
        
        logger = logging.getLogger('kinos_cli.launch_team')
        
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
        
        # Récupérer l'ID de la mission
        mission = web_instance.mission_service.get_mission_by_name(args.mission)
        if not mission:
            logger.error(f"Mission {args.mission} non trouvée")
            sys.exit(1)
        
        # Lancement de l'équipe avec gestion des erreurs détaillée
        try:
            result = web_instance.team_service.activate_team(mission['id'], args.team)
            
            if result:
                logger.info(f"Équipe {args.team} lancée avec succès")
                
                # Log detailed activation results
                for agent_result in result.get('activation_results', []):
                    if agent_result['success']:
                        logger.info(f"Agent {agent_result['agent']} activé avec succès")
                    else:
                        logger.error(f"Échec de l'activation de l'agent {agent_result['agent']}: {agent_result.get('error', 'Erreur inconnue')}")
                
                # Log team metrics if available
                if 'metrics' in result:
                    logger.info(f"Métriques de l'équipe : {result['metrics']}")
            else:
                logger.error(f"Échec du lancement de l'équipe {args.team}")
                sys.exit(1)
        
        except Exception as e:
            logger.error(f"Erreur lors du lancement de l'équipe : {e}")
            import traceback
            logger.error("Trace complète de l'erreur :")
            logger.error(traceback.format_exc())
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Erreur système lors du lancement de l'équipe : {e}")
        import traceback
        logger.error("Trace complète de l'erreur système :")
        logger.error(traceback.format_exc())
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
    parser = argparse.ArgumentParser(description="KinOS CLI - Team Launch")
    parser.add_argument('team', nargs='?', default='default', 
                       help='Team to launch (default: default)')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    try:
        # Configure logging
        logger = configure_cli_logger()
        logger.log(f"Starting KinOS CLI...", 'info')
        logger.log(f"Team: {args.team}", 'info')
        logger.log(f"Working directory: {os.getcwd()}", 'info')

        # Create service instances
        team_service = TeamService(None)
        agent_service = AgentService(None)

        # Launch team in current directory
        result = team_service.start_team(
            team_id=args.team, 
            base_path=os.getcwd()
        )

        if args.verbose:
            logger.log("Team launch details:", 'info')
            for agent_result in result.get('start_results', []):
                status = agent_result.get('status', 'unknown')
                agent = agent_result.get('agent', 'Unknown Agent')
                logger.log(f"Agent {agent}: {status}")

    except Exception as e:
        logger = configure_cli_logger()
        logger.log(f"Error launching team: {str(e)}", 'error')
        sys.exit(1)
