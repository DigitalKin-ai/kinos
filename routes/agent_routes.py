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
                    agent_name = agent_id.lower()
                    
                    # Read prompt file content
                    with open(os.path.join(prompts_dir, file), 'r', encoding='utf-8') as f:
                        prompt_content = f.read()
                    
                    # Get agent status if it exists
                    agent_status = web_instance.agent_service.get_agent_status().get(agent_name, {})
                    
                    agents.append({
                        'id': agent_id,
                        'name': agent_name,
                        'prompt': prompt_content,
                        'running': agent_status.get('running', False),
                        'last_run': agent_status.get('last_run'),
                        'status': agent_status.get('status', 'inactive')
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
                
            # Log initial state
            web_instance.log_message(f"Attempting to {action} agent {agent_id}", level='debug')
            
            # Convert agent ID to lowercase for case-insensitive matching
            agent_name = agent_id.lower()
            
            # Check if prompt file exists
            prompt_file = f"{agent_name}.md"
            prompt_path = os.path.join("prompts", prompt_file)
            
            if not os.path.exists(prompt_path):
                web_instance.log_message(f"Agent prompt file not found: {prompt_path}", level='error')
                raise ResourceNotFoundError(f"Agent {agent_id} not found")
            
            # Get or create agent instance
            agent = web_instance.agent_service.agents.get(agent_name)
            if not agent:
                # Initialize agent if needed
                web_instance.agent_service.init_agents(web_instance.config)
                agent = web_instance.agent_service.agents.get(agent_name)
                
            if not agent:
                raise ResourceNotFoundError(f"Failed to initialize agent {agent_id}")
            
            try:
                if action == 'start':
                    agent = web_instance.agent_service.agents[actual_agent_name]
                    agent.start()
                    thread = threading.Thread(
                        target=agent.run,
                        daemon=True,
                        name=f"Agent-{actual_agent_name}"
                    )
                    thread.start()
                    web_instance.log_message(f"Successfully started agent {actual_agent_name}", level='success')
                else:  # stop
                    agent = web_instance.agent_service.agents[actual_agent_name]
                    agent.stop()
                    web_instance.log_message(f"Successfully stopped agent {actual_agent_name}", level='success')
                
                return jsonify({'status': 'success'})
                
            except Exception as e:
                web_instance.log_message(
                    f"Error during {action} operation for {actual_agent_name}: {str(e)}\n"
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
