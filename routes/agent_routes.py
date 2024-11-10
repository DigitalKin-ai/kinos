import os
import threading
import traceback
from flask import jsonify, request
from utils.decorators import safe_operation
from utils.exceptions import ValidationError, ResourceNotFoundError, ServiceError
from utils.error_handler import ErrorHandler
from utils.path_manager import PathManager

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
            # Get prompts directory using PathManager
            prompts_dir = PathManager.get_prompts_path()
            
            # Validate prompts directory exists
            if not os.path.exists(prompts_dir):
                web_instance.log_message(f"Prompts directory not found: {prompts_dir}", level='error')
                return jsonify({'error': 'Prompts directory not found'}), 500

            # Verify directory permissions
            if not os.access(prompts_dir, os.R_OK | os.W_OK):
                web_instance.log_message(f"Insufficient permissions on prompts directory: {prompts_dir}", level='error')
                return jsonify({'error': 'Insufficient permissions on prompts directory'}), 500

            # Verify directory permissions
            if not os.access(prompts_dir, os.R_OK | os.W_OK):
                web_instance.log_message(f"Insufficient permissions on prompts directory: {prompts_dir}", level='error')
                return jsonify({'error': 'Insufficient permissions on prompts directory'}), 500

            agents = []
            # Get prompts directory using PathManager
            prompts_dir = PathManager.get_prompts_path()
            
            # Validate prompts directory exists
            if not os.path.exists(prompts_dir):
                web_instance.log_message(f"Prompts directory not found: {prompts_dir}", level='error')
                return jsonify({'error': 'Prompts directory not found'}), 500

            # Verify directory permissions
            if not os.access(prompts_dir, os.R_OK | os.W_OK):
                web_instance.log_message(f"Insufficient permissions on prompts directory: {prompts_dir}", level='error')
                return jsonify({'error': 'Insufficient permissions on prompts directory'}), 500

            # List all .md files in prompts directory
            for file in os.listdir(prompts_dir):
                if file.endswith('.md'):
                    agent_id = file[:-3]  # Remove .md
                    agent_name = agent_id.lower()
                    
                    try:
                        # Read prompt file content with absolute path
                        prompt_path = os.path.join(prompts_dir, file)
                        
                        # Verify file permissions
                        if not os.access(prompt_path, os.R_OK):
                            web_instance.log_message(f"Cannot read prompt file: {prompt_path}", level='error')
                            continue

                        # Read file with explicit UTF-8 encoding and error handling
                        try:
                            with open(prompt_path, 'r', encoding='utf-8', errors='replace') as f:
                                prompt_content = f.read()
                        except UnicodeError as ue:
                            web_instance.log_message(f"Unicode error reading {file}: {str(ue)}", level='error')
                            continue

                        # Validate prompt content
                        if not prompt_content.strip():
                            web_instance.log_message(f"Empty prompt file: {file}", level='warning')
                            continue
                        
                        # Get agent status if available
                        agent_status = {}
                        if hasattr(web_instance.agent_service, 'agents'):
                            agent = web_instance.agent_service.agents.get(agent_name)
                            if agent:
                                try:
                                    agent_status = {
                                        'running': agent.running if hasattr(agent, 'running') else False,
                                        'last_run': agent.last_run.isoformat() if hasattr(agent, 'last_run') and agent.last_run else None,
                                        'status': 'active' if getattr(agent, 'running', False) else 'inactive',
                                        'health': {
                                            'is_healthy': agent.is_healthy() if hasattr(agent, 'is_healthy') else True,
                                            'consecutive_no_changes': getattr(agent, 'consecutive_no_changes', 0),
                                            'current_interval': agent.calculate_dynamic_interval() if hasattr(agent, 'calculate_dynamic_interval') else None
                                        }
                                    }
                                except Exception as status_error:
                                    web_instance.log_message(f"Error getting status for {agent_name}: {str(status_error)}", level='error')
                                    agent_status = {
                                        'running': False,
                                        'status': 'error',
                                        'error': str(status_error)
                                    }
                        
                        agents.append({
                            'id': agent_id,
                            'name': agent_name,
                            'prompt': prompt_content,
                            'running': agent_status.get('running', False),
                            'last_run': agent_status.get('last_run'),
                            'status': agent_status.get('status', 'inactive'),
                            'health': agent_status.get('health', {'is_healthy': True}),
                            'file_path': prompt_path
                        })
                        
                        web_instance.log_message(f"Successfully loaded agent: {agent_name}", level='debug')
                        
                    except Exception as e:
                        web_instance.log_message(f"Error processing agent {agent_name}: {str(e)}", level='error')
                        continue
            
            # Sort agents by name
            agents.sort(key=lambda x: x['name'])
            
            web_instance.log_message(f"Successfully listed {len(agents)} agents", level='info')
            return jsonify(agents)
            
        except Exception as e:
            web_instance.log_message(f"Error listing agents: {str(e)}", level='error')
            return jsonify({'error': str(e)}), 500

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
