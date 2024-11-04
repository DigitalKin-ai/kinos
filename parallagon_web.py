from flask import Flask, render_template, jsonify, request, url_for, make_response
from flask_sock import Sock
from flask_sock import Sock
import threading
import time
import json
from datetime import datetime
from typing import Dict, Set, Any
from file_manager import FileManager
from llm_service import LLMService
from specifications_agent import SpecificationsAgent
from management_agent import ManagementAgent
from production_agent import ProductionAgent
from evaluation_agent import EvaluationAgent

class ParallagonWeb:
    def __init__(self, config):
        self.app = Flask(__name__)
        self.sock = Sock(self.app)
        self.clients = set()  # Store WebSocket clients
        self.sock = Sock(self.app)
        self.clients: Set[Any] = set()  # Store WebSocket clients
        self.last_content: Dict[str, str] = {}  # Cache last content
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
        @self.sock.route('/ws')
        def handle_websocket(ws):
            """Handle WebSocket connections"""
            self.clients.add(ws)
            self.log_message("New WebSocket client connected")
            
            # Send initial content
            initial_content = {
                'type': 'content_update',
                'content': {
                    'demande': self.file_manager.read_file('demande.md'),
                    'specifications': self.file_manager.read_file('specifications.md'),
                    'management': self.file_manager.read_file('management.md'),
                    'production': self.file_manager.read_file('production.md'),
                    'evaluation': self.file_manager.read_file('evaluation.md')
                }
            }
            ws.send(json.dumps(initial_content))
            
            try:
                while True:
                    message = ws.receive()
                    if message is not None:
                        self.process_websocket_message(message, ws)
                    else:
                        break
            except Exception as e:
                self.log_message(f"WebSocket error: {str(e)}")
            finally:
                self.clients.remove(ws)
                self.log_message("WebSocket client disconnected")

        @self.app.route('/')
        def home():
            # Initialize empty notifications list
            notifications = []  # Will be populated with any notifications to show
            return render_template('index.html', notifications=notifications)

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
            
        @self.app.route('/api/logs/export')
        def export_logs():
            try:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"parallagon-logs-{timestamp}.txt"
                
                # Format logs with timestamps
                formatted_logs = "\n".join(self.logs_buffer)
                
                # Create response with file download
                response = make_response(formatted_logs)
                response.headers["Content-Disposition"] = f"attachment; filename={filename}"
                response.headers["Content-Type"] = "text/plain"
                
                return response
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/logs/clear', methods=['POST'])
        def clear_logs():
            try:
                self.logs_buffer.clear()
                return jsonify({'status': 'success'})
            except Exception as e:
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
        self.running = True
        # Start content update loop
        def update_loop():
            while self.running:
                self.broadcast_content_update()
                time.sleep(1)  # Check for updates every second
                
        # Start update loop in separate thread
        threading.Thread(target=update_loop, daemon=True).start()
        
        # Start agents in separate threads
        for name, agent in self.agents.items():
            thread = threading.Thread(target=agent.run, daemon=True)
            thread.start()
            self.log_message(f"Agent {name} started")

    def stop_agents(self):
        self.running = False
        for agent in self.agents.values():
            agent.stop()

    def log_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs_buffer.append(log_entry)
        
        # Broadcast log to all WebSocket clients
        self.broadcast_message({
            'type': 'log',
            'timestamp': timestamp,
            'message': message
        })
        
        # Keep only last 100 logs
        if len(self.logs_buffer) > 100:
            self.logs_buffer.pop(0)
        print(log_entry)

    def broadcast_message(self, message: dict):
        """Broadcast message to all connected WebSocket clients"""
        disconnected = set()
        
        for client in self.clients:
            try:
                client.send(json.dumps(message))
            except Exception:
                disconnected.add(client)
                
        # Remove disconnected clients
        self.clients -= disconnected

    def process_websocket_message(self, message: str, ws):
        """Process incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'save_demande':
                content = data.get('content')
                if content:
                    success = self.file_manager.write_file('demande.md', content)
                    if success:
                        self.broadcast_content_update()
                        self.log_message("Demande updated successfully")
                    else:
                        self.log_message("Failed to update demande")
            elif message_type == 'ping':
                ws.send(json.dumps({'type': 'pong'}))
                        
        except Exception as e:
            self.log_message(f"Error processing WebSocket message: {str(e)}")

    def broadcast_content_update(self):
        """Broadcast content updates to all clients"""
        try:
            current_content = {
                'demande': self.file_manager.read_file('demande.md'),
                'specifications': self.file_manager.read_file('specifications.md'),
                'management': self.file_manager.read_file('management.md'),
                'production': self.file_manager.read_file('production.md'),
                'evaluation': self.file_manager.read_file('evaluation.md')
            }
            
            # Check for changes
            if current_content != self.last_content:
                self.last_content = current_content.copy()
                self.broadcast_message({
                    'type': 'content_update',
                    'content': current_content
                })
                
        except Exception as e:
            self.log_message(f"Error broadcasting content update: {str(e)}")

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
