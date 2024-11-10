import os
import threading
import traceback
from datetime import datetime
from flask import jsonify, request
from utils.decorators import safe_operation
from utils.exceptions import ValidationError, ResourceNotFoundError, ServiceError
from utils.error_handler import ErrorHandler
from utils.path_manager import PathManager

def register_agent_routes(app, web_instance):
    """Register all agent-related routes"""
    
    @app.route('/api/agents/start', methods=['POST'], endpoint='api_agents_start')
    @safe_operation()
    def start_all_agents():
        web_instance.agent_service.start_all_agents()
        return jsonify({'status': 'started'})
        
    @app.route('/api/agents/stop', methods=['POST'], endpoint='api_agents_stop')
    @safe_operation() 
    def stop_all_agents():
        web_instance.agent_service.stop_all_agents()
        return jsonify({'status': 'stopped'})
    @app.route('/api/agents/list', methods=['GET'], endpoint='api_agents_list')
    @safe_operation()
    def list_agents():
        try:
            # Get prompts directory using PathManager
            prompts_dir = PathManager.get_prompts_path()
            
            # Validate prompts directory exists and is accessible
            if not os.path.exists(prompts_dir):
                web_instance.log_message(f"Prompts directory not found: {prompts_dir}", 'error')
                return jsonify({'error': 'Prompts directory not found'}), 500
            if not os.access(prompts_dir, os.R_OK | os.W_OK):
                web_instance.log_message(f"Insufficient permissions on prompts directory: {prompts_dir}", 'error')
                return jsonify({'error': 'Insufficient permissions on prompts directory'}), 500

            # Verify directory permissions
            if not os.access(prompts_dir, os.R_OK | os.W_OK):
                web_instance.log_message(f"Insufficient permissions on prompts directory: {prompts_dir}", 'error')
                return jsonify({'error': 'Insufficient permissions on prompts directory'}), 500

            agents = []
            # Get prompts directory using PathManager
            prompts_dir = PathManager.get_prompts_path()

            # Verify directory permissions
            if not os.access(prompts_dir, os.R_OK | os.W_OK):
                web_instance.log_message(f"Insufficient permissions on prompts directory: {prompts_dir}", 'error')
                return jsonify({'error': 'Insufficient permissions on prompts directory'}), 500

            # Get prompts directory using PathManager
            prompts_dir = PathManager.get_prompts_path()
            
            # Validate prompts directory exists
            if not os.path.exists(prompts_dir):
                web_instance.log_message(f"Prompts directory not found: {prompts_dir}", 'error')
                return jsonify({'error': 'Prompts directory not found'}), 500

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
                            web_instance.log_message(f"Cannot read prompt file: {prompt_path}", 'error')
                            continue

                        # Read file with explicit UTF-8 encoding and error handling
                        try:
                            with open(prompt_path, 'r', encoding='utf-8', errors='replace') as f:
                                prompt_content = f.read()
                        except UnicodeError as ue:
                            web_instance.log_message(f"Unicode error reading {file}: {str(ue)}", 'error')
                            continue

                        # Validate prompt content
                        if not prompt_content.strip():
                            web_instance.log_message(f"Empty prompt file: {file}", 'warning')
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
                                    web_instance.logger.log(f"Error getting status for {agent_name}: {str(status_error)}")
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
                        
                        web_instance.log_message(f"Successfully loaded agent: {agent_name}", 'debug')
                        
                    except Exception as e:
                        web_instance.log_message(f"Error processing agent {agent_name}: {str(e)}", 'error')
                        continue
            
            # Sort agents by name
            agents.sort(key=lambda x: x['name'])
            
            web_instance.log_message(f"Successfully listed {len(agents)} agents", 'info')
            return jsonify(agents)
            
        except Exception as e:
            web_instance.log_message(f"Error listing agents: {str(e)}", 'error')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/agents/status', methods=['GET'], endpoint='api_agents_status')
    @safe_operation()
    def get_agents_status():
        try:
            # Verify agent_service is initialized
            if not hasattr(web_instance, 'agent_service'):
                error_details = {
                    'error': 'Agent service not initialized',
                    'type': 'ServiceError',
                    'details': {
                        'timestamp': datetime.now().isoformat(),
                        'additional_info': {
                            'web_instance_attributes': list(web_instance.__dict__.keys())
                        }
                    }
                }
                web_instance.log_message("Agent service not initialized")
                return jsonify(error_details), 500
                
            # Get status of all agents with detailed error handling
            try:
                status = {}
                for name, agent in web_instance.agent_service.agents.items():
                    try:
                        status[name] = {
                            'running': getattr(agent, 'running', False),
                            'last_run': agent.last_run.isoformat() if hasattr(agent, 'last_run') and agent.last_run else None,
                            'status': 'active' if getattr(agent, 'running', False) else 'inactive',
                            'health': {
                                'is_healthy': agent.is_healthy() if hasattr(agent, 'is_healthy') else True,
                                'consecutive_no_changes': getattr(agent, 'consecutive_no_changes', 0)
                            }
                        }
                    except Exception as agent_error:
                        web_instance.log_message(f"Error getting status for agent {name}: {str(agent_error)}", 'error')
                        status[name] = {
                            'running': False,
                            'status': 'error',
                            'error': str(agent_error)
                        }
                return jsonify(status)
                
            except Exception as e:
                error_details = {
                    'error': str(e),
                    'type': e.__class__.__name__,
                    'details': {
                        'traceback': traceback.format_exc(),
                        'timestamp': datetime.now().isoformat()
                    }
                }
                web_instance.log_message(f"Error getting agent status: {str(e)}", 'error')
                return jsonify(error_details), 500
                
        except Exception as e:
            error_details = {
                'error': str(e),
                'type': e.__class__.__name__,
                'details': {
                    'traceback': traceback.format_exc(),
                    'timestamp': datetime.now().isoformat()
                }
            }
            web_instance.log_message(f"Unhandled error in get_agents_status: {str(e)}", 'error')
            return jsonify(error_details), 500

    @app.route('/api/agent/<agent_id>/prompt', methods=['GET'], endpoint='api_agent_get_prompt')
    @safe_operation()
    def get_agent_prompt(agent_id):
        """Get the prompt for a specific agent"""
        try:
            # Normalize agent name
            agent_name = agent_id.lower()
            
            # Get prompts directory using PathManager
            prompts_dir = PathManager.get_prompts_path()
            
            # Build prompt file path
            prompt_file = os.path.join(prompts_dir, f"{agent_name}.md")
            
            # Check if file exists
            if not os.path.exists(prompt_file):
                return jsonify({'error': f'Prompt file not found for agent {agent_id}'}), 404
                
            # Read prompt content with explicit encoding
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt = f.read()
                return jsonify({'prompt': prompt})
                
            except Exception as e:
                web_instance.log_message(f"Error reading prompt file: {str(e)}", 'error')
                return jsonify({'error': f'Failed to read prompt file: {str(e)}'}), 500
                
        except Exception as e:
            web_instance.log_message(f"Error getting agent prompt: {str(e)}", 'error')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/agent/<agent_id>/prompt', methods=['POST'], endpoint='api_agent_save_prompt')
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

    @app.route('/api/agent/<agent_id>/<action>', methods=['POST'], endpoint='api_agent_control')
    @safe_operation()
    def control_agent(agent_id, action):
        try:
            if action not in ['start', 'stop']:
                raise ValidationError(f"Invalid action: {action}")
                
            # Convertir l'ID en minuscules pour la correspondance
            agent_name = agent_id.lower()
            
            # Vérifier que l'agent existe
            if agent_name not in web_instance.agent_service.agents:
                raise ResourceNotFoundError(f"Agent {agent_id} not found")
                
            agent = web_instance.agent_service.agents[agent_name]
            
            if action == 'start':
                if not agent.running:
                    agent.start()
                    thread = threading.Thread(
                        target=agent.run,
                        daemon=True,
                        name=f"Agent-{agent_name}"
                    )
                    thread.start()
            else:  # stop
                if agent.running:
                    agent.stop()
                    
            return jsonify({'status': 'success'})
            
        except Exception as e:
            web_instance.log_message(f"Error controlling agent {agent_id}: {str(e)}", 'error')
            return ErrorHandler.handle_error(e)
