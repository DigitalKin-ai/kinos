from flask import Flask, render_template, jsonify, request, make_response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import threading
import time
import os
import json
import git
from datetime import datetime
from typing import Dict, Any
from file_manager import FileManager
from llm_service import LLMService
from search_replace import SearchReplace
from parallagon_agent import ParallagonAgent
from specifications_agent import SpecificationsAgent
from management_agent import ManagementAgent
from production_agent import ProductionAgent
from evaluation_agent import EvaluationAgent

class ParallagonWeb:
    # Log level colors
    LOG_COLORS = {
        'info': 'blue',
        'success': 'green', 
        'warning': 'orange',
        'error': 'red',
        'debug': 'gray'
    }

    TEST_DATA = """# Demande de Revue de Connaissances LLM : L'Impact de l'IA Générative sur l'Industrie Musicale

## 1. Contexte de la demande

### Demandeur de la revue
- Nom, prénom : Dupont, Marie
- Fonction : Responsable Innovation
- Département : R&D
- Mail : m.dupont@entreprise.com

### Destinataire principal
[x] Équipe/service spécifique : Division Innovation & Stratégie Digitale

### But d'usage
[x] Support pour prise de décision
*Précision : Aide à la définition de notre stratégie d'intégration des IA génératives dans notre processus de production musicale*

### Qualité principale attendue
[x] Rigueur du raisonnement
*Critère de succès : La revue permet d'identifier clairement les opportunités et risques liés à l'IA générative en musique, avec une argumentation solide pour chaque point.*

### Niveau de profondeur
[x] Approfondi (10-15 pages)"""

    def __init__(self, config):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["200 per minute"]
        )
        self.content_cache = {}
        self.last_modified = {}
        self.last_content = {}
        self.setup_error_handlers()
        # Add file paths configuration
        self.file_paths = {
            "demande": "demande.md",
            "specifications": "specifications.md",
            "management": "management.md", 
            "production": "production.md",
            "evaluation": "evaluation.md"
        }
        self.file_manager = FileManager(self.file_paths)
        self.llm_service = LLMService(config["openai_api_key"])
        self.running = False
        self.agents = {}
        self.logs_buffer = []  # Store recent logs
        self.init_agents(config)
        self.setup_routes()

    def init_agents(self, config):
        """Initialisation des agents avec configuration standard"""
        try:
            self.log_message("Initializing agents...", level='info')
            # Initialize git repo
            try:
                self.repo = git.Repo(os.getcwd())
            except git.InvalidGitRepositoryError:
                self.repo = git.Repo.init(os.getcwd())
                self.log_message("Initialized new git repository")

            base_config = {
                "check_interval": 5,
                "anthropic_api_key": config["anthropic_api_key"],
                "openai_api_key": config["openai_api_key"],
                "logger": self.log_message,
                "repo": self.repo
            }
            
            self.agents = {
                "Specification": SpecificationsAgent({
                    **base_config,
                    "file_path": "specifications.md",
                    "watch_files": ["demande.md", "management.md", "production.md", "evaluation.md"]
                }),
                "Management": ManagementAgent({
                    **base_config,
                    "file_path": "management.md",
                    "watch_files": ["demande.md", "specifications.md", "production.md", "evaluation.md"]
                }),
                "Production": ProductionAgent({
                    **base_config,
                    "file_path": "production.md",
                    "watch_files": ["demande.md", "specifications.md", "management.md", "evaluation.md"]
                }),
                "Evaluation": EvaluationAgent({
                    **base_config,
                    "file_path": "evaluation.md",
                    "watch_files": ["demande.md", "specifications.md", "management.md", "production.md"]
                })
            }
            self.log_message("Agents initialized successfully", level='success')
            
        except Exception as e:
            self.log_message(f"Error initializing agents: {str(e)}", level='error')
            raise

    def handle_content_change(self, file_name: str, content: str, panel_name: str = None, flash: bool = False):
        """Handle content change notifications"""
        # Update cache
        self.content_cache[file_name] = content
        self.last_modified[file_name] = time.time()
        
        # Notify relevant agents
        for agent in self.agents.values():
            if hasattr(agent, 'watch_files') and file_name in agent.watch_files:
                agent.handle_file_change(file_name, content)

        # Ensure correct .md extension
        if not file_name.endswith('.md'):
            file_name = f"{file_name}.md"
            
        # Always add a notification when content changes
        notification = {
            'type': 'info',
            'message': f'Nouveau contenu dans {panel_name or file_name}',
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'operation': 'flash_tab',
            'status': file_name
        }
        
        self.logs_buffer.append(notification)
        self.log_message(f"File updated: {file_name}", operation="flash_tab", status=file_name)

    def setup_routes(self):
        @self.app.route('/api/test-data', methods=['POST'])
        def load_test_data():
            try:
                success = self.file_manager.write_file('demande', self.TEST_DATA)
                if success:
                    self.log_message("✨ Données de test chargées", level='success')
                    return jsonify({'status': 'success'})
                else:
                    return jsonify({'error': 'Failed to write test data'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        def load_test_data():
            try:
                success = self.file_manager.write_file('demande', self.TEST_DATA)
                if success:
                    self.log_message("✨ Données de test chargées")
                    return jsonify({'status': 'success'})
                else:
                    return jsonify({'error': 'Failed to write test data'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/reset', methods=['POST'])
        def reset_files():
            try:
                success = self.file_manager.reset_files()
                if success:
                    self.log_message("All files reset to initial state")
                    return jsonify({'status': 'success'})
                else:
                    return jsonify({'error': 'Failed to reset files'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/health')
        def health_check():
            return jsonify({
                'status': 'healthy',
                'running': self.running,
                'agents': {
                    name: {
                        'running': agent.should_run(),
                        'last_update': agent.last_update
                    }
                    for name, agent in self.agents.items()
                }
            })

        @self.app.route('/')
        def home():
            # Initialize empty notifications list
            notifications = []  # Will be populated with any notifications to show
            return render_template('index.html', notifications=notifications, 
                tab_ids={
                    'demande.md': 'tab-demande',
                    'specifications.md': 'tab-specifications', 
                    'management.md': 'tab-management',
                    'production.md': 'tab-production',
                    'evaluation.md': 'tab-evaluation'
                })

        @self.app.route('/api/status')
        def get_status():
            return jsonify({
                'running': self.running,
                'agents': {name: agent.should_run() for name, agent in self.agents.items()}
            })

        @self.app.route('/api/content')
        def get_content():
            try:
                content = {}
                for file_name in self.file_paths:
                    try:
                        content[file_name] = self.file_manager.read_file(file_name)
                        # Mettre en cache le contenu
                        self.content_cache[file_name] = content[file_name]
                        self.last_modified[file_name] = time.time()
                    except Exception as e:
                        self.log_message(f"Error reading {file_name}: {str(e)}")
                        content[file_name] = ""
                        
                return jsonify(content)
            except Exception as e:
                self.log_message(f"Error getting content: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/start', methods=['POST'])
        def start_agents():
            self.start_agents()
            return jsonify({'status': 'started'})

        @self.app.route('/api/stop', methods=['POST'])
        def stop_agents():
            self.stop_agents()
            return jsonify({'status': 'stopped'})

        @self.app.route('/api/logs')
        def get_logs():
            return jsonify({
                'logs': self.logs_buffer
            })
            
        @self.app.route('/api/logs/export')
        def export_logs():
            try:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"parallagon-logs-{timestamp}.txt"
                
                # Format logs with timestamps and colors
                formatted_logs = []
                for log in self.logs_buffer:
                    timestamp = log.get('timestamp', '')
                    level = log.get('level', 'info')
                    message = log.get('message', '')
                    formatted_logs.append(f"[{timestamp}] [{level.upper()}] {message}")
                
                # Join logs with newlines
                logs_content = "\n".join(formatted_logs)
                
                # Create response with file download
                response = make_response(logs_content)
                response.headers["Content-Disposition"] = f"attachment; filename={filename}"
                response.headers["Content-Type"] = "text/plain"
                
                self.log_message("Logs exported successfully", level='success')
                return response
            except Exception as e:
                self.log_message(f"Error exporting logs: {str(e)}", level='error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/logs/clear', methods=['POST'])
        def clear_logs():
            try:
                self.logs_buffer.clear()
                return jsonify({'status': 'success'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/notifications', methods=['GET'])
        def get_notifications():
            """Get pending notifications"""
            try:
                # Return filtered logs buffer directly
                notifications = [
                    {
                        'type': 'info',
                        'message': log.get('message', ''),
                        'timestamp': log.get('timestamp', '')
                    }
                    for log in self.logs_buffer
                    if log.get('operation') == 'flash_tab'
                ]
                
                # Clean buffer after sending
                self.logs_buffer = [
                    log for log in self.logs_buffer 
                    if log.get('operation') != 'flash_tab'
                ]
                
                return jsonify(notifications)
            except Exception as e:
                self.logger(f"Error getting notifications: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/demande', methods=['POST'])
        def update_demande():
            try:
                content = request.json.get('content')
                if not content:
                    return jsonify({'error': 'No content provided'}), 400
                    
                success = self.file_manager.write_file('demande.md', content)
                if success:
                    return jsonify({'status': 'success'})
                else:
                    return jsonify({'error': 'Failed to write file'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    def run(self, host='0.0.0.0', port=5000, **kwargs):
        """Run the Flask application with optional configuration parameters"""
        self.app.run(host=host, port=port, **kwargs)

    def start_agents(self):
        """Start all agents"""
        try:
            self.log_message("🚀 Démarrage des agents...", level='info')
            self.running = True
            
            # Start content update loop
            def update_loop():
                self.log_message("✓ Boucle de mise à jour démarrée", level='success')
                while self.running:
                    try:
                        self.check_content_updates()
                    except Exception as e:
                        self.log_message(f"❌ Erreur dans la boucle de mise à jour: {str(e)}", level='error')
                    time.sleep(1)  # Check every second
            
            # Start update loop in separate thread
            self.update_thread = threading.Thread(target=update_loop, daemon=True)
            self.update_thread.start()
            
            # Start agents in separate threads
            for name, agent in self.agents.items():
                try:
                    thread = threading.Thread(target=agent.run, daemon=True)
                    thread.start()
                    self.log_message(f"✓ Agent {name} démarré", level='success')
                except Exception as e:
                    self.log_message(f"❌ Erreur démarrage agent {name}: {str(e)}", level='error')
                    
            self.log_message("✨ Tous les agents sont actifs", level='success')
            
        except Exception as e:
            self.log_message(f"❌ Erreur globale: {str(e)}", level='error')
            raise

    def stop_agents(self):
        """Stop all agents and update loop"""
        self.running = False
        if hasattr(self, 'update_thread'):
            self.update_thread.join(timeout=2)  # Wait for update thread to finish
        for agent in self.agents.values():
            agent.stop()
        self.log_message("Agents stopped", level='info')

    def log_message(self, message, operation: str = None, status: str = None, level: str = 'info'):
        """Log a message with optional operation, status and color"""
        try:
            # Utiliser un format de date cohérent
            timestamp = datetime.now().strftime("%H:%M:%S")  # Format court HH:MM:SS
            
            # Determine color based on level
            color = self.LOG_COLORS.get(level, 'black')
            
            # Format log entry
            if operation and status:
                log_entry = {
                    'id': len(self.logs_buffer),
                    'timestamp': timestamp,
                    'message': f"{operation}: {status} - {message}",
                    'level': level,
                    'color': color
                }
            else:
                log_entry = {
                    'id': len(self.logs_buffer),
                    'timestamp': timestamp,
                    'message': message,
                    'level': level,
                    'color': color
                }
            
            # Add to logs buffer
            self.logs_buffer.append(log_entry)
            
            # Keep only last 100 logs
            if len(self.logs_buffer) > 100:
                self.logs_buffer = self.logs_buffer[-100:]
            
            # Print to console for debugging
            print(f"[{timestamp}] [{level}] {message}")
                
        except Exception as e:
            print(f"Error logging message: {str(e)}")

    def safe_operation(self, operation_func):
        """Decorator for safe operation execution with recovery"""
        def wrapper(*args, **kwargs):
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    return operation_func(*args, **kwargs)
                except Exception as e:
                    retry_count += 1
                    self.log_message(
                        str(e),
                        operation=operation_func.__name__,
                        status=f"RETRY {retry_count}/{max_retries}"
                    )
                    
                    if retry_count == max_retries:
                        self.log_message(
                            "Operation failed permanently",
                            operation=operation_func.__name__,
                            status="FAILED"
                        )
                        raise
                    
                    time.sleep(1)  # Wait before retry
                    
        return wrapper

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
                if file_name not in self.last_content or content != self.last_content[file_name]:
                    # Content modified or new file
                    self.handle_content_change(file_name, content)
                    self.last_content[file_name] = content
                    self.log_message(f"Content updated in {file_name}", level='info')

        except Exception as e:
            self.log_message(f"Error checking content updates: {str(e)}", level='error')

    def setup_error_handlers(self):
        @self.app.errorhandler(404)
        def not_found_error(error):
            return jsonify({'error': 'Resource not found'}), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': 'Internal server error'}), 500

        @self.app.errorhandler(Exception)
        def handle_exception(error):
            return jsonify({'error': str(error)}), 500

    def shutdown(self):
        """Graceful shutdown of the application"""
        try:
            # Stop all agents
            self.stop_agents()
            
            # Clear caches
            self.content_cache.clear()
            self.last_modified.clear()
            
            # Export final logs
            self.export_logs()
            
            self.log_message("Application shutdown complete")
        except Exception as e:
            self.log_message(f"Error during shutdown: {str(e)}")

    def get_app(self):
        """Return the Flask app instance"""
        return self.app

if __name__ == "__main__":
    # Load keys from .env file
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    config = {
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "openai_api_key": os.getenv("OPENAI_API_KEY")
    }
    
    # Validate API keys
    if not config["openai_api_key"] or config["openai_api_key"] == "your-api-key-here":
        raise ValueError("OPENAI_API_KEY not configured in .env file")
        
    if not config["anthropic_api_key"] or config["anthropic_api_key"] == "your-api-key-here":
        raise ValueError("ANTHROPIC_API_KEY not configured in .env file")
    
    app = ParallagonWeb(config)
    # Use Flask's development server when running directly 
    app.run(debug=True)
