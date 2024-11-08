import os
import threading
import traceback
from flask import jsonify, request
from utils.decorators import safe_operation
from utils.exceptions import ValidationError, ResourceNotFoundError, ServiceError
from utils.error_handler import ErrorHandler

def register_agent_routes(app, web_instance):
    """Register all agent-related routes"""
    
    @app.route('/api/agents/start', methods=['POST'])
    @safe_operation()
    def start_all_agents():
        web_instance.agent_service.start_all_agents()
        return jsonify({'status': 'started'})
        
    @app.route('/api/agents/stop', methods=['POST'])
    @safe_operation() 
    def stop_all_agents():
        web_instance.agent_service.stop_all_agents()
        return jsonify({'status': 'stopped'})
    @app.route('/api/agents/list', methods=['GET'])
    @safe_operation()
    def list_agents():
        try:
            prompts_dir = "prompts"
            agents = []
            
            # List all .md files in prompts directory
            for file in os.listdir(prompts_dir):
                if file.endswith('.md'):
                    agent_id = file[:-3]  # Remove .md
                    agent_name = agent_id.capitalize()
                    
                    # Read prompt file content
                    with open(os.path.join(prompts_dir, file), 'r', encoding='utf-8') as f:
                        prompt_content = f.read()
                    
                    agents.append({
                        'id': agent_id,
                        'name': agent_name,
                        'prompt': prompt_content,
                        'running': False  # Initial state
                    })
                    
            return jsonify(agents)
            
        except Exception as e:
            return ErrorHandler.handle_error(e)

    @app.route('/api/agents/status', methods=['GET'])
    @safe_operation()
    def get_agents_status():
        try:
            status = web_instance.agent_service.get_agent_status()
            return jsonify(status)
        except Exception as e:
            return ErrorHandler.handle_error(e)

    @app.route('/api/agent/<agent_id>/prompt', methods=['GET'])
    @safe_operation()
    def get_agent_prompt(agent_id):
        try:
            prompt = web_instance.agent_service.get_agent_prompt(agent_id)
            if prompt is None:
                raise ResourceNotFoundError(f"Agent {agent_id} not found")
            return jsonify({'prompt': prompt})
        except Exception as e:
            return ErrorHandler.handle_error(e)

    @app.route('/api/agent/<agent_id>/prompt', methods=['POST'])
    @safe_operation()
    def save_agent_prompt(agent_id):
        try:
            data = request.get_json()
            if not data or 'prompt' not in data:
                raise ValidationError("Prompt is required")
                
            success = web_instance.agent_service.save_agent_prompt(agent_id, data['prompt'])
            if not success:
                raise ServiceError("Failed to save prompt")
            return jsonify({'status': 'success'})
        except Exception as e:
            return ErrorHandler.handle_error(e)

    @app.route('/api/agent/<agent_id>/<action>', methods=['POST'])
    @safe_operation()
    def control_agent(agent_id, action):
        try:
            if action not in ['start', 'stop']:
                web_instance.log_message(f"Invalid action attempted: {action}", level='error')
                raise ValidationError(f"Invalid action: {action}")
                
            # Log l'état initial
            web_instance.log_message(f"Attempting to {action} agent {agent_id}", level='debug')
            web_instance.log_message(f"Available agents: {list(web_instance.agent_service.agents.keys())}", level='debug')
            
            # Convertir l'ID de l'agent
            agent_name = agent_id.capitalize()
            web_instance.log_message(f"Looking for agent with name: {agent_name}", level='debug')
            
            # Vérification détaillée de l'agent
            if agent_name not in web_instance.agent_service.agents:
                web_instance.log_message(
                    f"Agent {agent_name} not found in available agents: {list(web_instance.agent_service.agents.keys())}", 
                    level='error'
                )
                raise ResourceNotFoundError(f"Agent {agent_id} not found")
                
            # Log avant l'action
            web_instance.log_message(f"Found agent {agent_name}, attempting {action}", level='debug')
            
            try:
                if action == 'start':
                    agent = web_instance.agent_service.agents[agent_name]
                    agent.start()
                    thread = threading.Thread(
                        target=agent.run,
                        daemon=True,
                        name=f"Agent-{agent_name}"
                    )
                    thread.start()
                    web_instance.log_message(f"Successfully started agent {agent_name}", level='success')
                else:  # stop
                    agent = web_instance.agent_service.agents[agent_name]
                    agent.stop()
                    web_instance.log_message(f"Successfully stopped agent {agent_name}", level='success')
                
                return jsonify({'status': 'success'})
                
            except Exception as e:
                web_instance.log_message(
                    f"Error during {action} operation for {agent_name}: {str(e)}\n"
                    f"Stack trace: {traceback.format_exc()}", 
                    level='error'
                )
                raise
                
        except Exception as e:
            web_instance.log_message(
                f"Failed to {action} agent {agent_id}: {str(e)}\n"
                f"Stack trace: {traceback.format_exc()}", 
                level='error'
            )
            return ErrorHandler.handle_error(e)
