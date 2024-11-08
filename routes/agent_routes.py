import os
from flask import jsonify, request
from utils.decorators import safe_operation
from utils.error_handler import ErrorHandler
from utils.exceptions import ValidationError, ResourceNotFoundError, ServiceError

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
                raise ValidationError(f"Invalid action: {action}")
                
            success = web_instance.agent_service.control_agent(agent_id, action)
            if not success:
                raise ServiceError(f"Failed to {action} agent {agent_id}")
            return jsonify({'status': 'success'})
        except Exception as e:
            return ErrorHandler.handle_error(e)
