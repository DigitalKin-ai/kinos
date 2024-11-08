from flask import jsonify, request
from utils.decorators import safe_operation

def register_agent_routes(app, web_instance):
    @app.route('/api/agents/status', methods=['GET'])
    @safe_operation()
    def get_agents_status():
        status = web_instance.agent_service.get_agent_status()
        return jsonify(status)

    @app.route('/api/agent/<agent_id>/prompt', methods=['GET'])
    @safe_operation()
    def get_agent_prompt(agent_id):
        prompt = web_instance.agent_service.get_agent_prompt(agent_id)
        if prompt is None:
            return jsonify({'error': 'Agent not found'}), 404
        return jsonify({'prompt': prompt})

    @app.route('/api/agent/<agent_id>/prompt', methods=['POST'])
    @safe_operation()
    def save_agent_prompt(agent_id):
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Prompt is required'}), 400
            
        success = web_instance.agent_service.save_agent_prompt(agent_id, data['prompt'])
        if not success:
            return jsonify({'error': 'Failed to save prompt'}), 500
        return jsonify({'status': 'success'})

    @app.route('/api/agent/<agent_id>/<action>', methods=['POST'])
    @safe_operation()
    def control_agent(agent_id, action):
        if action not in ['start', 'stop']:
            return jsonify({'error': 'Invalid action'}), 400
            
        success = web_instance.agent_service.control_agent(agent_id, action)
        if not success:
            return jsonify({'error': f'Failed to {action} agent'}), 500
        return jsonify({'status': 'success'})
