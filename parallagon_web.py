from flask import Flask, render_template, jsonify, request, url_for
import threading
import time
from file_manager import FileManager
from llm_service import LLMService
from specifications_agent import SpecificationsAgent
from management_agent import ManagementAgent
from production_agent import ProductionAgent
from evaluation_agent import EvaluationAgent

class ParallagonWeb:
    def __init__(self, config):
        self.app = Flask(__name__)
        self.file_manager = FileManager()
        self.llm_service = LLMService(config["openai_api_key"])
        self.running = False
        self.agents = {}
        self.logs_buffer = []  # Store recent logs
        self.init_agents(config)
        self.setup_routes()

    def init_agents(self, config):
        """Initialisation des agents avec configuration standard"""
        base_config = {
            "check_interval": 5,
            "anthropic_api_key": config["anthropic_api_key"],
            "openai_api_key": config["openai_api_key"],
            "logger": self.log_message
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

    def setup_routes(self):
        @self.app.route('/')
        def home():
            return render_template('index.html')

        @self.app.route('/api/status')
        def get_status():
            return jsonify({
                'running': self.running,
                'agents': {name: agent.should_run() for name, agent in self.agents.items()}
            })

        @self.app.route('/api/content')
        def get_content():
            return jsonify({
                'demande': self.file_manager.read_file('demande.md'),
                'specifications': self.file_manager.read_file('specifications.md'),
                'management': self.file_manager.read_file('management.md'),
                'production': self.file_manager.read_file('production.md'),
                'evaluation': self.file_manager.read_file('evaluation.md')
            })

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

    def run(self, host='0.0.0.0', port=5000):
        self.app.run(host=host, port=port)

    def start_agents(self):
        self.running = True
        # Démarrer les agents dans des threads séparés
        for name, agent in self.agents.items():
            thread = threading.Thread(target=agent.run, daemon=True)
            thread.start()

    def stop_agents(self):
        self.running = False
        for agent in self.agents.values():
            agent.stop()

    def log_message(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs_buffer.append(log_entry)
        # Keep only last 100 logs
        if len(self.logs_buffer) > 100:
            self.logs_buffer.pop(0)
        print(log_entry)

    def get_app(self):
        """Return the Flask app instance"""
        return self.app

if __name__ == "__main__":
    config = {
        "anthropic_api_key": "your-api-key-here",
        "openai_api_key": "your-api-key-here"
    }
    app = ParallagonWeb(config)
    # Use Flask's development server when running directly 
    app.run(debug=True)
