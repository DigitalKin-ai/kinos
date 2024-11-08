from flask import jsonify, request
from utils.decorators import safe_operation
from utils.error_handler import ErrorHandler
from utils.exceptions import ValidationError, ResourceNotFoundError, ServiceError

def register_agent_routes(app, web_instance):
    """Register all agent-related routes"""
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
