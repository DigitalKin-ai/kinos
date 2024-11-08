from flask import jsonify, request
from typing import Dict, Any

def register_agent_routes(app, web_instance):
    @app.route('/api/agents/status', methods=['GET'])
    def get_agents_status():
        """Get status of all agents"""
        try:
            status = {
                name.lower(): {
                    'running': agent.running,
                    'last_run': agent.last_run.isoformat() if agent.last_run else None,
                    'last_change': agent.last_change.isoformat() if agent.last_change else None
                }
                for name, agent in web_instance.agents.items()
            }
            return jsonify(status)
        except Exception as e:
            web_instance.log_message(f"Failed to get agents status: {str(e)}", level='error')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/agent/<agent_id>/prompt', methods=['GET', 'POST'])
    def handle_agent_prompt(agent_id):
        """Handle agent prompt operations"""
        try:
            agent_name = agent_id.capitalize()
            if agent_name not in web_instance.agents:
                return jsonify({'error': 'Agent not found'}), 404

            if request.method == 'GET':
                prompt = web_instance.agents[agent_name].get_prompt()
                return jsonify({'prompt': prompt})
            else:
                data = request.get_json()
                if not data or 'prompt' not in data:
                    return jsonify({'error': 'Prompt is required'}), 400
                
                success = web_instance.agents[agent_name].save_prompt(data['prompt'])
                if success:
                    web_instance.log_message(f"Prompt saved for agent {agent_name}", level='success')
                    return jsonify({'status': 'success'})
                return jsonify({'error': 'Failed to save prompt'}), 500
                
        except Exception as e:
            web_instance.log_message(f"Error handling agent prompt: {str(e)}", level='error')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/agent/<agent_id>/<action>', methods=['POST'])
    def control_agent(agent_id, action):
        """Control agent operations"""
        return web_instance.handle_agent_control(agent_id, action)
