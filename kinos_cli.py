import argparse
import os
import sys
import time
import threading
from datetime import datetime
from services.team_service import TeamService
from services.mission_service import MissionService
from services.agent_service import AgentService
from utils.logger import configure_cli_logger
from utils.path_manager import PathManager

class KinosCLI:
    def __init__(self, force_color=None):
        # Use the new configure_cli_logger method
        self.logger = configure_cli_logger(force_color)
        
        # Initialize dataset service first
        from services.dataset_service import DatasetService
        self.dataset_service = DatasetService(self)
        
        # Verify dataset service is available
        if not self.dataset_service.is_available():
            self.logger.log("Warning: Dataset service not available", 'warning')
        
        self.mission_service = MissionService()
        
        # Update mission path configuration using PathManager
        self.config = {
            "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
            "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
            "paths": {
                "missions_dir": PathManager.get_mission_path(""),
                "prompts_dir": PathManager.get_prompts_path(),
                "logs_dir": PathManager.get_logs_path()
            }
        }
        
        # Créer explicitement un AgentService
        self.agent_service = AgentService(self)
        
        # Ajouter une méthode log directement à l'instance
        self.log = self.logger.log
        
        # Passer self avec l'agent_service et config ajoutés
        self.team_service = TeamService(self)

    def launch_team(self, mission_name, team_name, verbose=False, dry_run=False, timeout=None, log_file=None, base_path=None):
        """
        Lance une équipe pour une mission spécifique et affiche les logs en continu
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

            # Résoudre le chemin de la mission en utilisant PathManager
            try:
                mission_path = PathManager.get_mission_path(mission_name, base_path)
                
                # Créer le dossier de mission s'il n'existe pas
                if not os.path.exists(mission_path):
                    self.logger.log(f"Création du dossier de mission : {mission_path}", 'info')
                    os.makedirs(mission_path, exist_ok=True)
                
                # Vérifier les permissions
                if not os.access(mission_path, os.R_OK | os.W_OK):
                    self.logger.log(f"Erreur : Permissions insuffisantes sur {mission_path}", 'error')
                    sys.exit(1)
                
            except Exception as path_error:
                self.logger.log(f"Erreur de résolution du chemin de mission : {str(path_error)}", 'error')
                sys.exit(1)

            if dry_run:
                self.logger.log(f"Mode simulation : Lancement de l'équipe {team_name} pour la mission {mission_name}", 'info')
                return

            # Lancement de l'équipe
            self.logger.log(f"Lancement de l'équipe {team_name} pour la mission {mission_name}...", 'info')
            result = self.team_service.activate_team(mission['id'], team_name)
            
            if not result:
                self.logger.log("Échec de l'activation de l'équipe", 'error')
                sys.exit(1)

            self.team_service.start_team(mission['id'], team_name, mission_path=mission_path) 

            self.logger.log(f"✓ Équipe {team_name} activée et démarée. Démarrage des agents...", 'success')
            self.logger.log(f"Dossier de mission : {mission_path}", 'info')
            self.logger.log("Appuyez sur CTRL+C pour arrêter les agents", 'info')
            
            # Boucle principale d'affichage des logs
            try:
                while True:
                    # Obtenir le statut de tous les agents
                    status = self.agent_service.get_agent_status()
                    
                    # Afficher le statut de chaque agent
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
                    
                    # Afficher une ligne de séparation
                    self.logger.log("-" * 80, 'info')
                    
                    # Attendre avant la prochaine mise à jour
                    time.sleep(60)

            except KeyboardInterrupt:
                self.logger.log("\nArrêt demandé. Arrêt des agents...", 'warning')
                self.agent_service.stop_all_agents()
                self.logger.log("Tous les agents ont été arrêtés.", 'success')
                sys.exit(0)

        except Exception as e:
            self.logger.log(f"Erreur lors du lancement de l'équipe : {e}", 'error')
            self.agent_service.stop_all_agents()  # S'assurer que les agents sont arrêtés en cas d'erreur
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

    def start_specific_agent(self, mission_name: str, agent_name: str):
        """
        Start a specific agent for a given mission
        
        Args:
            mission_name (str): Name of the mission
            agent_name (str): Name of the agent to start
        """
        try:
            # Validate mission exists
            mission = self.mission_service.get_mission_by_name(mission_name)
            if not mission:
                self.logger.log(f"Mission '{mission_name}' not found.", 'error')
                sys.exit(1)

            # Resolve mission path using PathManager
            try:
                mission_path = PathManager.get_mission_path(mission_name)
                
                # Validate mission directory
                if not os.path.exists(mission_path):
                    self.logger.log(f"Mission directory not found: {mission_path}", 'error')
                    sys.exit(1)
                
                if not os.access(mission_path, os.R_OK | os.W_OK):
                    self.logger.log(f"Insufficient permissions on: {mission_path}", 'error')
                    sys.exit(1)
                    
            except Exception as path_error:
                self.logger.log(f"Error resolving mission path: {str(path_error)}", 'error')
                sys.exit(1)

            # Normalize agent name
            normalized_agent_name = agent_name.lower().replace('agent', '').strip()
            
            # Verify agent exists
            available_agents = self.agent_service.get_available_agents()
            if normalized_agent_name not in available_agents:
                self.logger.log(f"Agent '{normalized_agent_name}' not found.", 'error')
                self.logger.log(f"Available agents: {', '.join(available_agents)}", 'info')
                sys.exit(1)

            # Attempt to start the agent
            success = self.agent_service.toggle_agent(
                agent_name=normalized_agent_name, 
                action='start', 
                mission_dir=mission_path
            )

            if success:
                self.logger.log(
                    f"✅ Agent {normalized_agent_name} started successfully for mission {mission_name}", 
                    'success'
                )
                
                # Start a thread to monitor the agent
                def monitor_agent():
                    try:
                        while True:
                            status = self.agent_service.get_agent_status(normalized_agent_name)
                            
                            # Display agent status
                            running = status.get('running', False)
                            health = status.get('health', {})
                            last_run = status.get('last_run', 'Never')
                            
                            status_str = "🟢 Active" if running else "🔴 Inactive"
                            health_str = "✅ Healthy" if health.get('is_healthy', True) else "❌ Degraded"
                            
                            self.logger.log(
                                f"Agent {normalized_agent_name} Status:\n"
                                f"  Running: {status_str}\n"
                                f"  Health: {health_str}\n"
                                f"  Last Run: {last_run}\n"
                                f"  Consecutive No Changes: {health.get('consecutive_no_changes', 0)}",
                                'info'
                            )
                            
                            # Wait before next status check
                            time.sleep(60)
                            
                    except KeyboardInterrupt:
                        self.logger.log(f"\nStopping monitoring for agent {normalized_agent_name}", 'warning')
                    except Exception as e:
                        self.logger.log(f"Error monitoring agent: {str(e)}", 'error')

                # Start monitoring thread
                monitor_thread = threading.Thread(target=monitor_agent, daemon=True)
                monitor_thread.start()

                # Keep main thread running
                try:
                    monitor_thread.join()
                except KeyboardInterrupt:
                    self.logger.log("\nAgent monitoring stopped by user.", 'warning')
                    self.agent_service.toggle_agent(normalized_agent_name, 'stop')
                    sys.exit(0)

            else:
                self.logger.log(f"Failed to start agent {normalized_agent_name}", 'error')
                sys.exit(1)

        except Exception as e:
            self.logger.log(f"Error starting agent: {str(e)}", 'error')
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
    # Parse arguments with color support
    parser = argparse.ArgumentParser(description="KinOS CLI - Gestion des équipes d'agents")
    
    # Add color control arguments
    parser.add_argument('--color', 
                        choices=['auto', 'always', 'never'], 
                        default='auto', 
                        help='Control color output')
    
    # Rest of the existing argument parsing...
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')
    
    # Nouvelle commande list globale
    list_parser = subparsers.add_parser('list', help='Lister tous les éléments')
    
    # Sous-commande pour lancer une équipe
    team_parser = subparsers.add_parser('team', help='Commandes liées aux équipes')
    team_subparsers = team_parser.add_subparsers(dest='team_command')
    
    launch_parser = team_subparsers.add_parser('launch', help='Lancer une équipe pour une mission')
    launch_parser.add_argument('--team', required=True, help='Nom de l\'équipe')
    launch_parser.add_argument('--verbose', action='store_true', help='Mode débogage détaillé')
    launch_parser.add_argument('--dry-run', action='store_true', help='Simulation sans exécution')
    launch_parser.add_argument('--base-path', help='Chemin de base personnalisé', default=None)

    # Sous-commande pour les agents
    agent_parser = subparsers.add_parser('agent', help='Commandes liées aux agents')
    agent_subparsers = agent_parser.add_subparsers(dest='agent_command')

    # Commande list pour les agents
    list_parser = agent_subparsers.add_parser('list', help='Lister tous les agents disponibles')

    # Commande start pour démarrer un agent spécifique
    start_parser = agent_subparsers.add_parser('start', help='Démarrer un agent spécifique')
    start_parser.add_argument('--mission', required=True, help='Nom de la mission')
    start_parser.add_argument('--name', required=True, help='Nom de l\'agent à démarrer')

    # Sous-commande pour lister les missions
    missions_parser = subparsers.add_parser('missions', help='Commandes liées aux missions')
    missions_subparsers = missions_parser.add_subparsers(dest='missions_command')
    missions_list_parser = missions_subparsers.add_parser('list', help='Lister toutes les missions')

    # Sous-commande pour lister les équipes
    teams_parser = subparsers.add_parser('teams', help='Commandes liées aux équipes')
    teams_subparsers = teams_parser.add_subparsers(dest='teams_command')
    teams_list_parser = teams_subparsers.add_parser('list', help='Lister toutes les équipes')

    # Parse arguments
    args = parser.parse_args()

    # Determine color configuration
    force_color = None
    if args.color == 'always':
        force_color = True
    elif args.color == 'never':
        force_color = False

    # Create CLI instance with color configuration
    cli = KinosCLI(force_color=force_color)

    # Dispatch des commandes
    if args.command == 'list':
        # Lister tous les éléments
        cli.list_agents()
        cli.list_missions()
        cli.list_teams()
    elif args.command == 'team' and args.team_command == 'launch':
        cli.launch_team(
            team_name=args.team, 
            base_path=args.base_path,
            verbose=args.verbose,
            dry_run=args.dry_run
        )
    elif args.command == 'agent' and args.agent_command == 'list':
        cli.list_agents()
    elif args.command == 'agent' and args.agent_command == 'start':
        cli.start_specific_agent(
            mission_name=args.mission, 
            agent_name=args.name
        )
    elif args.command == 'missions' and args.missions_command == 'list':
        cli.list_missions()
    elif args.command == 'teams' and args.teams_command == 'list':
        cli.list_teams()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
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
    main()
