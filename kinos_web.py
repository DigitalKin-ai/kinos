import os
import time
import threading
import traceback
from datetime import datetime

from flask import Flask, jsonify, render_template, request
from utils.path_manager import PathManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from services.file_manager import FileManager

from utils.error_handler import ErrorHandler
from utils.exceptions import *
from utils.logger import Logger

from services.agent_service import AgentService
from services.mission_service import MissionService
from services.notification_service import NotificationService
from services.file_manager import FileManager as FileService

from routes.agent_routes import register_agent_routes
from routes.mission_routes import register_mission_routes
from routes.notification_routes import register_notification_routes
from routes.view_routes import register_view_routes

class KinOSWeb:
    # Log level colors
    LOG_COLORS = {
        'info': 'blue',
        'success': 'green', 
        'warning': 'orange',
        'error': 'red',
        'debug': 'gray',
        'redacteur': 'purple'
    }

    def _register_routes(self):
        """Register all route blueprints"""
        
        if hasattr(self, '_routes_registered'):
            return
            
        register_agent_routes(self.app, self)
        register_mission_routes(self.app, self)
        register_notification_routes(self.app, self)
        register_view_routes(self.app, self)
        
        self._routes_registered = True

        # Log registered routes for debugging
        self.log_message("Registered routes:", 'info')
        for rule in self.app.url_map.iter_rules():
            self.log_message(f"  {rule.endpoint}: {rule.methods} {rule}", 'info')

        # Add error handlers
        @self.app.errorhandler(404)
        @self.app.endpoint('error_404')
        def not_found_error(error):
            """Handle 404 errors"""
            self.log_message(f"404 Error: {str(error)}", 'error')
            return jsonify({
                'error': 'Not Found',
                'message': str(error),
                'type': '404',
                'timestamp': datetime.now().isoformat()
            }), 404

        @self.app.errorhandler(500)
        @self.app.endpoint('error_500')
        def internal_error(error):
            """Handle 500 errors"""
            self.log_message(f"500 Error: {str(error)}", 'error')
            return jsonify({
                'error': 'Internal Server Error',
                'message': str(error),
                'type': '500',
                'timestamp': datetime.now().isoformat()
            }), 500

        # Mark routes as registered
        self._routes_registered = True

        # Log registered routes for debugging
        self.log_message("Registered routes:", 'info')
        for rule in self.app.url_map.iter_rules():
            self.log_message(f"  {rule.endpoint}: {rule.methods} {rule}", 'info')
        
    def _initialize_components(self, config):
        """Initialize all required components"""
        try:
            # Initialize basic services first
            self.logger.log("Initializing core components...", 'info')
            
            # Get prompts directory using PathManager
            prompts_dir = PathManager.get_prompts_path()
            
            if not os.path.exists(prompts_dir):
                os.makedirs(prompts_dir)
                self.log_message("Created prompts directory", 'info')
                return

            # Initialize agents in inactive state
            try:
                self.agent_service.init_agents(config)
                self.logger.log("Agents initialized in inactive state", 'success')
            except ValueError as e:
                if "No mission selected" in str(e):
                    self.logger.log("No mission selected - agents will be initialized when mission is selected", 'warning')
                else:
                    raise
            except Exception as e:
                self.logger.log(f"Warning: Agent initialization failed: {str(e)}", 'warning')
                
            self.logger.log("Core components initialized successfully", 'success')
            
        except Exception as e:
            self.logger.log(f"Error initializing components: {str(e)}", 'error')
            raise ServiceError(f"Failed to initialize components: {str(e)}")

    def log_message(self, message: str, level: str = 'info', **kwargs) -> None:
        """Log a message with optional level"""
        try:
            # Format timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Get color for level
            color = self.LOG_COLORS.get(level, 'white')
            
            # Format the message
            formatted_message = f"[{timestamp}] [{level.upper()}] {message}"
            
            # Print to console
            self.logger.log(formatted_message)
            
            # Log to file if needed
            try:
                with open('agent_operations.log', 'a', encoding='utf-8') as f:
                    f.write(f"{formatted_message}\n")
            except Exception as file_error:
                print(f"Error writing to log file: {file_error}")
                
        except Exception as e:
            # Fallback to basic print if logging fails
            print(f"Logging error: {e}")
            print(f"Original message: {message}")

    def _load_test_data(self):
        """Load test data from template file"""
        try:
            test_data_path = os.path.join("templates", "test_data", "demande_test_1.md")
            if not os.path.exists(test_data_path):
                self.log_message(f"Test data file not found: {test_data_path}", 'error')
                return ""
                
            with open(test_data_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.log_message(f"Error loading test data: {str(e)}", 'error')
            return ""

    def _log_initialization(self, component: str, success: bool, error: Exception = None) -> None:
        """Centralized initialization logging"""
        if success:
            self.logger.log(f"✓ {component} initialized successfully", 'success')
        else:
            self.logger.log(f"❌ {component} initialization failed: {str(error)}", 'error')

    def __init__(self, config):
        # Store config for agent initialization
        self.config = config
        
        # Initialize logger first
        self.logger = Logger()
        
        # Get project paths using PathManager
        project_root = PathManager.get_project_root()
        template_dir = os.path.join(project_root, 'templates')
        static_dir = os.path.join(project_root, 'static')
        
        # Add debug logging for paths
        self.logger.log(f"Project root: {project_root}", 'debug')
        self.logger.log(f"Template directory: {template_dir}", 'debug')
        self.logger.log(f"Static directory: {static_dir}", 'debug')
        
        # Verify paths exist
        if not os.path.exists(template_dir):
            raise RuntimeError(f"Template directory not found: {template_dir}")
        if not os.path.exists(static_dir):
            raise RuntimeError(f"Static directory not found: {static_dir}")
            
        # Get and store project paths
        self.project_root = PathManager.get_project_root()
        self.template_dir = PathManager.get_templates_path()
        self.static_dir = PathManager.get_static_path()
        
        # Add debug logging for paths
        self.logger.log(f"Project root: {self.project_root}", 'debug')
        self.logger.log(f"Template directory: {self.template_dir}", 'debug')
        self.logger.log(f"Static directory: {self.static_dir}", 'debug')
        
        # Verify paths exist
        if not os.path.exists(self.template_dir):
            raise RuntimeError(f"Template directory not found: {self.template_dir}")
        if not os.path.exists(self.static_dir):
            raise RuntimeError(f"Static directory not found: {self.static_dir}")
        
        # Add debug logging for paths
        self.logger.log(f"Project root: {project_root}", 'debug')
        self.logger.log(f"Template directory: {template_dir}", 'debug')
        self.logger.log(f"Static directory: {static_dir}", 'debug')
        
        # Get project paths using PathManager
        project_root = PathManager.get_project_root()
        template_dir = PathManager.get_templates_path()
        static_dir = PathManager.get_static_path()
        
        # Get project paths using PathManager
        project_root = PathManager.get_project_root()
        template_dir = PathManager.get_templates_path()
        static_dir = PathManager.get_static_path()
        
        # Initialize Flask with explicit template and static folders
        self.app = Flask(__name__,
                        template_folder=template_dir,
                        static_folder=static_dir,
                        static_url_path='/static')
        CORS(self.app)
        
        # Initialize rate limiter
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["1000 per minute"]
        )
        
        # Register routes and handlers
        self._register_routes()
        self._register_error_handlers()
        
        # Add debug logging for paths
        self.logger.log(f"Template directory: {template_dir}", 'debug')
        self.logger.log(f"Static directory: {static_dir}", 'debug')
        
        # Import dataset service
        from services.dataset_service import DatasetService
        
        # Initialize services in correct order without circular dependencies
        self.mission_service = MissionService()  # No dependencies
        self.dataset_service = DatasetService(self)  # Initialize dataset service
        
        # Initialize file manager directly
        self.file_manager = FileManager(web_instance=self)
        
        # Initialize other services that depend on web_instance
        self.file_service = FileService(self)
        self.notification_service = NotificationService(self)
        self.agent_service = AgentService(self)
        
        # Initialize rate limiter
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["1000 per minute"]
        )
        
        # Register routes and handlers
        self._register_routes()
        self._register_error_handlers()
        
        # Initialize components with config
        self._initialize_components(config)

    def init_agents(self, config):
        """Initialisation des agents avec configuration standard"""
        try:
            self.log_message("Initializing agents...", 'info')
            
            # S'assurer que le dossier missions existe
            os.makedirs("missions", exist_ok=True)

            # Obtenir la liste des missions
            missions = self.mission_service.get_all_missions()
            if not missions:
                self.log_message("No missions available. Please create a mission first.", 'warning')
                return

            # Utiliser la première mission par défaut ou la mission courante si définie
            mission_name = getattr(self, 'current_mission', missions[0]['name']) if missions else None
            if not mission_name:
                raise ValueError("No mission available for initialization")

            # Load agent intervals from config
            intervals_config = self._load_intervals_config()
                
            # Create mission directory path
            mission_dir = os.path.join("missions", mission_name)
            
            base_config = {
                "check_interval": 10,
                "anthropic_api_key": config["anthropic_api_key"],
                "openai_api_key": config["openai_api_key"],
                "logger": self.log_message,
                "mission_name": mission_name,
                "web_instance": self  # Add web_instance to base config
            }

            # Load prompts from files
            def load_prompt(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    self.log_message(f"Error loading prompt from {file_path}: {e}", 'error')
                    return ""

            # Get prompts directory using PathManager
            prompts_dir = PathManager.get_prompts_path()
            
            if not os.path.exists(prompts_dir):
                os.makedirs(prompts_dir)
                self.log_message("Created prompts directory", 'info')
                return

            def _initialize_agent(self, agent_name: str, config: dict) -> Optional[AiderAgent]:
                """Centralized agent initialization"""
                try:
                    agent_config = {
                        **config,
                        "name": agent_name,
                        "prompt": self._load_agent_prompt(agent_name)
                    }
                    agent = AiderAgent(agent_config)
                    self.log_message(f"✓ Agent {agent_name} initialized", 'success')
                    return agent
                except Exception as e:
                    self.log_message(f"Error initializing agent {agent_name}: {str(e)}", 'error')
                    return None

            for file in os.listdir(prompts_dir):
                if file.endswith('.md'):
                    agent_name = file[:-3].lower()  # Remove .md extension
                    agent = self._initialize_agent(agent_name, base_config)
                    if agent:
                        self.agents[agent_name] = agent

            if not self.agents:
                self.log_message("No agents were initialized", 'warning')
                return

            # Vérifier que tous les agents sont correctement initialisés
            for name, agent in self.agents.items():
                if not agent:
                    raise ValueError(f"Agent {name} non initialisé correctement")
                self.log_message(f"✓ Agent {name} initialisé", 'success')

            self.log_message("Agents initialized successfully", 'success')
            
        except Exception as e:
            self.log_message(f"Error initializing agents: {str(e)}", 'error')
            import traceback
            self.log_message(traceback.format_exc(), 'error')
            raise


    def toggle_agent(self, agent_id: str, action: str) -> bool:
        """
        Toggle an individual agent's state
        
        Args:
            agent_id: ID of the agent to toggle
            action: 'start' or 'stop'
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            agent_name = agent_id.lower()
            if agent_name not in self.agents:
                self.log_message(f"Agent {agent_id} not found", 'error')
                return False
                
            agent = self.agents[agent_name]
            
            if action == 'start':
                if not agent.running:
                    agent.start()
                    thread = threading.Thread(
                        target=agent.run,
                        daemon=True,
                        name=f"Agent-{agent_name}"
                    )
                    thread.start()
                    self.log_message(f"Agent {agent_name} started", 'success')
            elif action == 'stop':
                if agent.running:
                    agent.stop()
                    self.log_message(f"Agent {agent_name} stopped", 'info')
            
            return True
            
        except Exception as e:
            self.log_message(f"Failed to toggle agent {agent_id}: {str(e)}", 'error')
            return False

    def setup_routes(self):
        """Configure all application routes"""

        @self.app.route('/explorer')
        def explorer():
            """Explorer interface"""
            return render_template('explorer.html')

        @self.app.route('/api/missions/<int:mission_id>/files/<path:file_path>')
        def get_mission_file_content(mission_id, file_path):
            """Get content of a specific file in mission directory"""
            try:
                mission = self.mission_service.get_mission(mission_id)
                if not mission:
                    return jsonify({'error': 'Mission not found'}), 404

                # Sécuriser le chemin du fichier
                safe_path = os.path.normpath(file_path)
                if safe_path.startswith('..'):
                    return jsonify({'error': 'Invalid file path'}), 400

                full_path = os.path.join("missions", mission['name'], safe_path)
                if not os.path.exists(full_path):
                    return jsonify({'error': 'File not found'}), 404

                # Vérifier l'extension
                ext = os.path.splitext(full_path)[1].lower()
                if ext not in {'.md', '.txt', '.py', '.js', '.json', '.yaml', '.yml'}:
                    return jsonify({'error': 'Unsupported file type'}), 400

                # Lire le contenu du fichier
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                return content, 200, {'Content-Type': 'text/plain'}

            except Exception as e:
                self.log_message(f"Error reading file content: {str(e)}", 'error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/<int:mission_id>/files')
        def get_mission_files(mission_id):
            """Get all files in mission directory respecting ignore patterns"""
            try:
                mission = self.mission_service.get_mission(mission_id)
                if not mission:
                    return jsonify({'error': 'Mission not found'}), 404

                # Extensions de fichiers texte supportées
                text_extensions = {'.md', '.txt', '.py', '.js', '.json', '.yaml', '.yml'}
                
                # Dossier racine de la mission
                mission_dir = os.path.abspath(os.path.join("missions", mission['name']))
                if not os.path.exists(mission_dir):
                    return jsonify({'error': 'Mission directory not found'}), 404
                    
                # Get all files
                files = []
                try:
                    for root, _, filenames in os.walk(mission_dir):
                        for filename in filenames:
                            if filename.endswith(('.md', '.txt', '.py', '.js', '.json', '.yaml', '.yml')):
                                try:
                                    full_path = os.path.join(root, filename)
                                    relative_path = os.path.relpath(full_path, mission_dir)
                                
                                    file_info = {
                                        'name': filename,
                                        'path': relative_path,
                                        'relativePath': relative_path,
                                        'size': os.path.getsize(full_path),
                                        'modified': os.path.getmtime(full_path)
                                    }
                                    files.append(file_info)
                                    web_instance.logger.log(f"Added file: {filename}", 'debug')
                                
                                except (OSError, IOError) as e:
                                    web_instance.logger.log(f"Error processing file {filename}: {str(e)}", 'error')
                                    continue

                    # Sort files by path
                    files.sort(key=lambda x: x['path'])
                
                    web_instance.logger.log(f"Found {len(files)} files in mission {mission['name']}", 'info')
                    return jsonify(files)

                except Exception as e:
                    web_instance.logger.log(f"Error listing files: {str(e)}", 'error')
                    return jsonify({'error': f'Error listing files: {str(e)}'}), 500

            except Exception as e:
                web_instance.logger.log(f"Unexpected error in get_mission_files: {str(e)}", 'error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/<int:mission_id>/content', methods=['GET'])
        def get_mission_content(mission_id):
            try:
                mission = self.mission_service.get_mission(mission_id)
                if not mission:
                    return jsonify({'error': 'Mission not found'}), 404
                    
                content = {}
                for file_type, file_path in mission['files'].items():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content[file_type] = f.read()
                    except Exception as e:
                        self.log_message(f"Error reading {file_type} file: {str(e)}", 'error')
                        content[file_type] = ""
                        
                return jsonify(content)
                
            except Exception as e:
                self.log_message(f"Error getting mission content: {str(e)}", 'error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/<int:mission_id>/content/<file_type>', methods=['POST'])
        def save_mission_content(mission_id, file_type):
            try:
                data = request.get_json()
                if not data or 'content' not in data:
                    return jsonify({'error': 'Content is required'}), 400
                    
                success = self.mission_service.save_mission_file(
                    mission_id,
                    file_type,
                    data['content']
                )
                
                if not success:
                    return jsonify({'error': 'Failed to save content'}), 500
                    
                self.log_message(f"Saved {file_type} content for mission {mission_id}", 'success')
                return jsonify({'status': 'success'})
                
            except Exception as e:
                self.log_message(f"Error saving mission content: {str(e)}", 'error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions', methods=['GET'])
        def get_missions():
            try:
                missions = self.mission_service.get_all_missions()
                if missions is None:
                    return jsonify({'error': 'Failed to fetch missions'}), 500
                    
                return jsonify(missions)
                
            except Exception as e:
                self.log_message(f"Error getting missions: {str(e)}", 'error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/validate-directory', methods=['POST'])
        def validate_mission_directory():
            """Validate that a directory contains required mission files"""
            try:
                data = request.get_json()
                if not data or 'path' not in data:
                    return jsonify({'error': 'Path is required'}), 400
                    
                path = data['path']
                
                # Get required files dynamically from web instance
                required_files = list(web_instance.get_required_agent_files().values())
                
                missing_files = []
                for file in required_files:
                    if not os.path.isfile(os.path.join(path, file)):
                        missing_files.append(file)
                        
                if missing_files:
                    return jsonify({
                        'error': f'Dossier invalide. Fichiers manquants : {", ".join(missing_files)}'
                    }), 400
                    
                return jsonify({'status': 'valid'})
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/get-directory-path', methods=['POST'])
        def get_directory_path():
            """Get full path for a directory selected in the frontend"""
            try:
                data = request.get_json()
                if not data or 'name' not in data:
                    return jsonify({'error': 'Directory name is required'}), 400
                    
                directory_name = data['name']
                
                # Chercher le dossier dans les emplacements possibles
                possible_paths = [
                    os.path.abspath(directory_name),  # Chemin absolu
                    os.path.join(os.getcwd(), directory_name),  # Relatif au dossier courant
                    os.path.expanduser(f"~/{directory_name}"),  # Dans le home
                    os.path.join(os.path.expanduser("~/Documents"), directory_name),  # Dans Documents
                    os.path.join(os.path.expanduser("~"), "Documents", directory_name)  # Autre syntaxe pour Documents
                ]
                
                # Debug log
                self.log_message(f"Searching for directory: {directory_name}")
                self.log_message(f"Possible paths: {possible_paths}")
                
                # Trouver le premier chemin valide
                for path in possible_paths:
                    if os.path.isdir(path):
                        self.log_message(f"Found valid path: {path}")
                        return jsonify({'path': path})
                
                self.log_message(f"No valid path found for: {directory_name}", 'error')        
                return jsonify({'error': 'Directory not found'}), 404
                
            except Exception as e:
                self.log_message(f"Error getting directory path: {str(e)}", 'error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/link', methods=['POST'])
        def create_mission_link():
            """Create a mission from an external directory"""
            try:
                data = request.get_json()
                if not data or 'path' not in data:
                    return jsonify({'error': 'External path is required'}), 400
                    
                external_path = data['path']
                mission_name = data.get('name')  # Optional
                
                # Create mission link
                mission = self.mission_service.create_mission_link(
                    external_path=external_path,
                    mission_name=mission_name
                )
                
                self.log_message(
                    f"Created link to external mission at {external_path}", 
                    'success'
                )
                return jsonify(mission), 201
                
            except Exception as e:
                self.log_message(f"Error creating mission link: {str(e)}", 'error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions', methods=['POST'])
        def create_mission():
            try:
                data = request.get_json()
                if not data or 'name' not in data:
                    return jsonify({'error': 'Name is required'}), 400
                    
                # Validate mission name
                mission_name = data['name'].strip()
                if not mission_name:
                    return jsonify({'error': 'Mission name cannot be empty'}), 400
                    
                # Check if mission already exists
                if self.mission_service.mission_exists(mission_name):
                    return jsonify({'error': 'Mission with this name already exists'}), 409
                    
                # Create mission in database
                mission = self.mission_service.create_mission(
                    name=mission_name,
                    description=data.get('description')
                )
                
                # Update FileManager's current mission
                self.file_manager.current_mission = mission_name
                
                # Create mission files
                if not self.file_manager.create_mission_files(mission_name):
                    # Rollback database creation if file creation fails
                    self.mission_service.delete_mission(mission['id'])
                    self.file_manager.current_mission = None
                    return jsonify({'error': 'Failed to create mission files'}), 500
                
                self.log_message(f"Mission '{mission_name}' created successfully", 'success')
                return jsonify(mission), 201
                
            except Exception as e:
                self.log_message(f"Error creating mission: {str(e)}", 'error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/<int:mission_id>', methods=['GET'])
        def get_mission(mission_id):
            try:
                mission = self.mission_service.get_mission(mission_id)
                if not mission:
                    return jsonify({'error': 'Mission not found'}), 404
                    
                # Update FileManager's current mission
                self.file_manager.current_mission = mission['name']
                
                # Update agent paths when mission changes
                self.update_agent_paths(mission['name'])
                
                # Stop agents if they're running
                was_running = self.running
                if was_running:
                    self.stop_agents()
                    
                # Start agents again if they were running
                if was_running:
                    self.start_agents()
                    
                self.log_message(f"Mission {mission['name']} loaded successfully", 'success')
                return jsonify(mission)
                
            except Exception as e:
                self.log_message(f"Error getting mission: {str(e)}", 'error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/<int:mission_id>', methods=['PUT'])
        def update_mission(mission_id):
            try:
                data = request.get_json()
                mission = self.mission_service.update_mission(
                    mission_id,
                    name=data.get('name'),
                    description=data.get('description'),
                    status=data.get('status')
                )
                if not mission:
                    return jsonify({'error': 'Mission not found'}), 404
                    
                self.log_message(f"Mission {mission_id} updated", 'success')
                return jsonify(mission)
                
            except Exception as e:
                self.log_message(f"Error updating mission: {str(e)}", 'error')
                return jsonify({'error': str(e)}), 500
            

        @self.app.route('/api/missions/<int:mission_id>/test-data', methods=['POST'])
        def load_test_data(mission_id):
            """Load test data into the current mission"""
            try:
                # Vérifier que la mission existe
                mission = self.mission_service.get_mission(mission_id)
                if not mission:
                    return jsonify({'error': 'Mission not found'}), 404

                # Load test data from file
                test_data = self._load_test_data()

                # Sauvegarder dans le fichier demande.md de la mission
                mission_path = os.path.join("missions", mission['name'])
                demande_path = os.path.join(mission_path, "demande.md")

                try:
                    with open(demande_path, 'w', encoding='utf-8') as f:
                        f.write(test_data)

                    self.log_message(f"✓ Données de test chargées pour la mission {mission['name']}", 'success')
                    return jsonify({'status': 'success'})

                except Exception as write_error:
                    self.log_message(f"❌ Erreur d'écriture des données de test: {str(write_error)}", 'error')
                    return jsonify({'error': f'File write error: {str(write_error)}'}), 500

            except Exception as e:
                self.log_message(f"❌ Erreur chargement données test: {str(e)}", 'error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/<int:mission_id>/reset', methods=['POST'])
        def reset_mission_files(mission_id):
            try:
                mission = self.mission_service.get_mission(mission_id)
                if not mission:
                    return jsonify({'error': 'Mission not found'}), 404

                self.log_message(f"Files reset for mission {mission['name']}", 'success')
                return jsonify({'status': 'success'})
                
            except Exception as e:
                self.log_message(f"Error resetting files: {str(e)}", 'error')
                return jsonify({'error': str(e)}), 500





        @self.app.route('/api/content', methods=['GET'])
        def handle_content():
            try:
                # Skip if no mission selected
                if not hasattr(self, 'current_mission') or not self.current_mission:
                    return jsonify({})  # Return empty object if no mission

                content = {}
                mission_dir = os.path.join("missions", self.current_mission)

                # List of files to check
                files_to_check = {
                    'demande': 'demande.md',
                    'specifications': 'specifications.md', 
                    'management': 'management.md',
                    'production': 'production.md',
                    'evaluation': 'evaluation.md',
                    'suivi': 'suivi.md'
                }

                # Check each file
                for panel_id, filename in files_to_check.items():
                    file_path = os.path.join(mission_dir, filename)
                    try:
                        if os.path.exists(file_path):
                            # Get last modified time
                            last_modified = os.path.getmtime(file_path)
                            
                            # Check if file has been modified
                            if panel_id not in self.last_modified or self.last_modified[panel_id] != last_modified:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    new_content = f.read()
                                    
                                # If content has changed
                                if panel_id not in self.content_cache or self.content_cache[panel_id] != new_content:
                                    self.log_message(
                                        f"File changed: {filename} in mission {self.current_mission}",
                                        'info'
                                    )
                                    content[panel_id] = new_content
                                    self.content_cache[panel_id] = new_content
                                    self.last_modified[panel_id] = last_modified
                                    
                    except Exception as e:
                        self.log_message(f"Error reading {filename}: {str(e)}", 'error')
                        # Continue with other files even if one fails

                return jsonify(content)
                    
            except Exception as e:
                self.log_message(f"Error handling content: {str(e)}", 'error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/agent/<agent_id>/prompt', methods=['GET'])
        def get_agent_prompt(agent_id):
            """Get the prompt for a specific agent"""
            try:
                agent_name = agent_id.lower()
                if agent_name not in self.agents:
                    return jsonify({'error': 'Agent not found'}), 404
                    
                prompt = self.agents[agent_name].get_prompt()
                return jsonify({'prompt': prompt})
                
            except Exception as e:
                self.log_message(f"Error getting agent prompt: {str(e)}", 'error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/agent/<agent_id>/prompt', methods=['POST'])
        def save_agent_prompt(agent_id):
            """Save the prompt for a specific agent"""
            try:
                data = request.get_json()
                if not data or 'prompt' not in data:
                    return jsonify({'error': 'Prompt is required'}), 400
                    
                agent_name = agent_id.capitalize()
                if agent_name not in self.agents:
                    return jsonify({'error': 'Agent not found'}), 404
                    
                success = self.agents[agent_name].save_prompt(data['prompt'])
                if success:
                    self.log_message(f"Prompt saved for agent {agent_name}", 'success')
                    return jsonify({'status': 'success'})
                else:
                    return jsonify({'error': 'Failed to save prompt'}), 500
                    
            except Exception as e:
                self.log_message(f"Error saving agent prompt: {str(e)}", 'error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/changes')
        def get_changes():
            """Return and clear pending changes"""
            try:
                notifications = self.notification_service.get_notifications()
                return jsonify(notifications)
            except Exception as e:
                self.logger.log(f"Error in get_changes: {str(e)}", 'error')
                return jsonify([])

        @self.app.route('/api/notifications', methods=['GET', 'POST'])
        @self.limiter.limit("500 per minute")
        def handle_notifications():
            """Handle notifications GET and POST"""
            if request.method == 'GET':
                """Get pending notifications"""
                try:
                    # Récupérer les notifications en attente
                    notifications = []
                    
                    # Ajouter les notifications de la queue
                    while self.notifications_queue:
                        notification = self.notifications_queue.pop(0)
                        notifications.append(notification)
                        self.log_message(f"Sending notification: {notification}", 'debug')
                        
                    # Debug log
                    if notifications:
                        self.log_message(f"Sending {len(notifications)} notifications to frontend", 'debug')
                        
                    return jsonify(notifications)
                    
                except Exception as e:
                    self.log_message(f"Error getting notifications: {str(e)}", 'error')
                    # Retourner une liste vide au lieu d'une erreur 500
                    return jsonify([])
                    
            else:  # POST
                """Handle content change notifications from agents"""
                try:
                    data = request.get_json()
                    self.log_message(f"Received notification: {data}", 'debug')
                    
                    # Validate required fields
                    required_fields = ['file_path', 'content', 'panel', 'message']
                    if not all(field in data for field in required_fields):
                        missing = [f for f in required_fields if f not in data]
                        self.log_message(f"Missing required fields: {missing}", 'error')
                        return jsonify({'error': f'Missing required fields: {missing}'}), 400
                        
                    # Add notification to queue with explicit flash and status
                    notification = {
                        'type': data.get('type', 'info'),
                        'message': data['message'],
                        'panel': data['panel'],
                        'content': data['content'],
                        'flash': data.get('flash', True),
                        'timestamp': datetime.now().strftime("%H:%M:%S"),
                        'id': len(self.notifications_queue),
                        'status': data['file_path']  # Important for tab flashing
                    }
                    
                    self.log_message(f"Adding notification to queue: {notification}", 'debug')
                    self.notifications_queue.append(notification)
                    
                    # Update content cache
                    if data['content'].strip():
                        self.content_cache[data['file_path']] = data['content']
                        self.last_modified[data['file_path']] = time.time()
                        
                    return jsonify({'status': 'success'})
                    
                except Exception as e:
                    self.log_message(f"Error handling notification: {str(e)}", 'error')
                    return jsonify({'error': str(e)}), 500


    def _register_routes(self):
        """Register all route blueprints"""
        
        # First register core routes directly on the app
        @self.app.route('/api/status', methods=['GET'], endpoint='api_core_status')  # Changed endpoint name
        def get_status():
            """Get server and agents status"""
            try:
                status = {
                    'server': {
                        'running': True,
                        'timestamp': datetime.now().isoformat()
                    },
                    'agents': {}
                }
                
                # Add agent status if agent service is initialized
                if hasattr(self, 'agent_service'):
                    for name, agent in self.agent_service.agents.items():
                        status['agents'][name] = {
                            'running': agent.running if hasattr(agent, 'running') else False,
                            'last_run': agent.last_run.isoformat() if hasattr(agent, 'last_run') and agent.last_run else None,
                            'status': 'active' if getattr(agent, 'running', False) else 'inactive',
                            'health': {
                                'is_healthy': agent.is_healthy() if hasattr(agent, 'is_healthy') else True,
                                'consecutive_no_changes': getattr(agent, 'consecutive_no_changes', 0)
                            }
                        }
                    
                return jsonify(status)
                
            except Exception as e:
                self.log_message(f"Error getting status: {str(e)}", 'error')
                return jsonify({
                    'error': str(e),
                    'type': e.__class__.__name__,
                    'details': {
                        'traceback': traceback.format_exc(),
                        'timestamp': datetime.now().isoformat()
                    }
                }), 500

        # Add error handlers
        @self.app.errorhandler(404)
        def not_found_error(error):
            """Handle 404 errors"""
            self.log_message(f"404 Error: {str(error)}", 'error')
            return jsonify({
                'error': 'Not Found',
                'message': str(error),
                'type': '404',
                'timestamp': datetime.now().isoformat()
            }), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            """Handle 500 errors"""
            self.log_message(f"500 Error: {str(error)}", 'error')
            return jsonify({
                'error': 'Internal Server Error',
                'message': str(error),
                'type': '500',
                'timestamp': datetime.now().isoformat()
            }), 500

        # Then register blueprint routes only once
        if not hasattr(self, '_routes_registered'):
            register_agent_routes(self.app, self)
            register_mission_routes(self.app, self)
            register_notification_routes(self.app, self)
            register_view_routes(self.app, self)
            self._routes_registered = True

        # Log registered routes for debugging
        self.log_message("Registered routes:", 'info')
        for rule in self.app.url_map.iter_rules():
            self.log_message(f"  {rule.endpoint}: {rule.methods} {rule}", 'info')

    def _handle_api_error(self, operation: str, error: Exception, status_code: int = 500) -> tuple:
        """Centralized API error handling"""
        error_details = {
            'error': str(error),
            'type': error.__class__.__name__,
            'details': {
                'traceback': traceback.format_exc(),
                'timestamp': datetime.now().isoformat(),
                'operation': operation
            }
        }
        self.logger.log(f"Error in {operation}: {str(error)}", 'error')
        return jsonify(error_details), status_code

    def _register_error_handlers(self):
        """Register error handlers for different types of exceptions"""
        
        @self.app.errorhandler(Exception)
        def handle_exception(error):
            """Handle any uncaught exception"""
            return self._handle_api_error('uncaught_exception', error)
            
            # Log the full error details
            self.logger.log(f"Detailed error info:", 'error')
            self.logger.log(f"Type: {error_details['type']}", 'error')
            self.logger.log(f"Traceback:\n{error_details['traceback']}", 'error')
            
            return jsonify(error_details), 500

        @self.app.errorhandler(500)
        def internal_error(error):
            """Handle internal server errors"""
            self.logger.log(f"500 Error: {str(error)}", 'error')
            
            error_details = {
                'error': str(error),
                'type': '500 Internal Server Error',
                'traceback': traceback.format_exc(),
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(error_details), 500

        @self.app.errorhandler(ValidationError)
        def handle_validation_error(error):
            return ErrorHandler.validation_error(str(error))
            
        @self.app.errorhandler(ResourceNotFoundError)
        def handle_not_found_error(error):
            return ErrorHandler.not_found_error(str(error))
            
        @self.app.errorhandler(ServiceError)
        def handle_service_error(error):
            return ErrorHandler.service_error(str(error))
            
    def _initialize_components(self, config):
        """Initialize all required components"""
        try:
            # Initialize basic services first
            self.logger.log("Initializing core components...", 'info')
            
            # Get prompts directory using PathManager
            prompts_dir = PathManager.get_prompts_path()
            
            if not os.path.exists(prompts_dir):
                os.makedirs(prompts_dir)
                self.log_message("Created prompts directory", 'info')
                return

            # Initialize agents in inactive state
            try:
                self.agent_service.init_agents(config)
                self.logger.log("Agents initialized in inactive state", 'success')
            except ValueError as e:
                if "No mission selected" in str(e):
                    self.logger.log("No mission selected - agents will be initialized when mission is selected", 'warning')
                else:
                    raise
            except Exception as e:
                self.logger.log(f"Warning: Agent initialization failed: {str(e)}", 'warning')
                
            self.logger.log("Core components initialized successfully", 'success')
            
        except Exception as e:
            self.logger.log(f"Error initializing components: {str(e)}", 'error')
            raise ServiceError(f"Failed to initialize components: {str(e)}")
            
    def run(self, host='0.0.0.0', port=8000, debug=False):
        """Run the Flask application"""
        try:
            self.app.run(host=host, port=port, debug=debug)
        except Exception as e:
            self.logger.log(f"Error running application: {str(e)}", 'error')
            raise ServiceError(f"Failed to start application: {str(e)}")
            
    def reinitialize_agents(self):
        """Reinitialize agents with current mission configuration"""
        try:
            if hasattr(self, 'agent_service'):
                self.agent_service.init_agents({
                    "anthropic_api_key": self.config["anthropic_api_key"],
                    "openai_api_key": self.config["openai_api_key"]
                })
                self.logger.log("Agents reinitialized with new mission", 'success')
        except Exception as e:
            self.logger.log(f"Error reinitializing agents: {str(e)}", 'error')

    def shutdown(self):
        """Graceful shutdown of the application"""
        try:
            # Stop all agents
            self.agent_service.stop_all_agents()
            
            # Cleanup services
            self.notification_service.cleanup()
            self.file_service.cleanup()
            
            self.logger.log("Application shutdown complete", 'info')
            
        except Exception as e:
            self.logger.log(f"Error during shutdown: {str(e)}", 'error')
            raise ServiceError(f"Failed to shutdown cleanly: {str(e)}")




    def check_content_updates(self):
        """Check for content updates"""
        try:
            # Read current content of all files
            current_content = {}
            for file_name, path in self.file_paths.items():
                content = self.file_manager.read_file(file_name)
                if content is not None:
                    current_content[file_name] = content

            # Compare with last known content
            if not hasattr(self, 'last_content'):
                self.last_content = {}

            # Check changes for each file
            for file_name, content in current_content.items():
                if content is None:
                    continue
                    
                if (file_name not in self.last_content or 
                    content != self.last_content[file_name]):
                    # Content modified or new file
                    self.handle_content_change(
                        file_name, 
                        content,
                        panel_name=file_name.split('.')[0].capitalize()
                    )
                    self.last_content[file_name] = content
                    self.log_message(f"Content updated in {file_name}")

        except Exception as e:
            self.log_message(f"Error checking content updates: {str(e)}", 'error')

    def setup_error_handlers(self):
        @self.app.errorhandler(404)
        def not_found_error(error):
            self.log_message(f"404 Error: {str(error)}", 'error')
            return jsonify({'error': 'Resource not found'}), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            self.log_message(f"500 Error: {str(error)}", 'error')
            import traceback
            self.log_message(traceback.format_exc(), 'error')
            return jsonify({'error': 'Internal server error'}), 500

        @self.app.errorhandler(Exception)
        def handle_exception(error):
            self.log_message(f"Unhandled Exception: {str(error)}", 'error')
            import traceback
            self.log_message(traceback.format_exc(), 'error')
            return jsonify({'error': str(error)}), 500


    def shutdown(self):
        """Graceful shutdown of the application"""
        try:
            # Stop all agents
            self.stop_agents()
            
            # Clear caches
            self.content_cache.clear()
            self.last_modified.clear()
            
            self.log_message("Application shutdown complete")
        except Exception as e:
            self.log_message(f"Error during shutdown: {str(e)}")



    def get_app(self):
        """Return the Flask app instance"""
        return self.app

if __name__ == "__main__":
    from config import Config
    
    # Validate configuration
    Config.validate()
    
    # Create and run app
    app = KinOSWeb({
        "anthropic_api_key": Config.ANTHROPIC_API_KEY,
        "openai_api_key": Config.OPENAI_API_KEY
    })
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
