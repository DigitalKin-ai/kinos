from flask import jsonify, request
from typing import Dict, Any
from utils.decorators import safe_operation
from utils.exceptions import ValidationError

def _validate_team_request(team_id: str, action: str = None) -> bool:
    """Centralized validation of team requests"""
    if not team_id or not isinstance(team_id, str):
        return False
    if action and action not in ['start', 'stop', 'status']:
        return False
    return True

def _validate_team_configuration(team_id: str) -> Dict[str, Any]:
    """Validate and return team configuration with enhanced checks"""
    predefined_teams = {
        "book_writing": {
            "name": "Book Writing Team",
            "required_agents": [
                "SpecificationsAgent", 
                "ManagementAgent", 
                "EvaluationAgent"
            ],
            "optional_agents": [
                "ChroniqueurAgent", 
                "DocumentalisteAgent", 
                "DuplicationAgent"
            ]
        },
        "literature_review": {
            "name": "Literature Review Team",
            "required_agents": [
                "SpecificationsAgent", 
                "ManagementAgent", 
                "EvaluationAgent"
            ],
            "optional_agents": [
                "ChroniqueurAgent", 
                "DocumentalisteAgent", 
                "DuplicationAgent"
            ]
        },
        "coding": {
            "name": "Coding Team",
            "required_agents": [
                "SpecificationsAgent", 
                "ManagementAgent", 
                "EvaluationAgent"
            ],
            "optional_agents": [
                "ChroniqueurAgent", 
                "DocumentalisteAgent", 
                "ProductionAgent", 
                "TesteurAgent"
            ]
        }
    }
    
    if team_id not in predefined_teams:
        raise ValidationError(f"Invalid team: {team_id}")
    
    return predefined_teams[team_id]

def register_team_routes(app, web_instance):
    """Register all team-related routes"""
    
    @app.errorhandler(404)
    def team_not_found(error):
        return jsonify({
            'error': 'Team not found',
            'details': str(error)
        }), 404

    @app.errorhandler(400) 
    def bad_request(error):
        return jsonify({
            'error': 'Bad request',
            'details': str(error)
        }), 400

    @app.route('/api/teams', methods=['GET'], endpoint='api_teams_list')
    @safe_operation()
    def get_teams():
        """Get list of available teams"""
        try:
            teams = [
                {
                    "id": "book_writing",
                    "name": "Book Writing Team",
                    "description": "Content creation and documentation",
                    "agents": [
                        "SpecificationsAgent",
                        "ManagementAgent", 
                        "EvaluationAgent",
                        "ChroniqueurAgent",
                        "DocumentalisteAgent",
                        "DuplicationAgent",
                        "RedacteurAgent",
                        "ValidationAgent"
                    ]
                },
                {
                    "id": "literature_review",
                    "name": "Literature Review Team",
                    "description": "Research and analysis",
                    "agents": [
                        "SpecificationsAgent",
                        "ManagementAgent",
                        "EvaluationAgent", 
                        "ChroniqueurAgent",
                        "DocumentalisteAgent",
                        "DuplicationAgent",
                        "RedacteurAgent",
                        "ValidationAgent"
                    ]
                },
                {
                    "id": "coding",
                    "name": "Coding Team",
                    "description": "Software development",
                    "agents": [
                        "SpecificationsAgent",
                        "ManagementAgent",
                        "EvaluationAgent",
                        "ChroniqueurAgent", 
                        "DocumentalisteAgent",
                        "DuplicationAgent",
                        "ProductionAgent",
                        "TesteurAgent",
                        "ValidationAgent"
                    ]
                }
            ]
            return jsonify(teams)
        except Exception as e:
            web_instance.log_message(f"Error getting teams: {str(e)}", 'error')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/teams/<team_id>/start', methods=['POST'], endpoint='api_team_start')
    @safe_operation()
    def start_team(team_id):
        """Start all agents in a team"""
        try:
            # Get team configuration
            teams = {
                "book_writing": ["specifications", "management", "evaluation", "chroniqueur", 
                               "documentaliste", "duplication", "redacteur", "validation"],
                "literature_review": ["specifications", "management", "evaluation", "chroniqueur",
                                    "documentaliste", "duplication", "redacteur", "validation"],
                "coding": ["specifications", "management", "evaluation", "chroniqueur",
                          "documentaliste", "duplication", "production", "testeur", "validation"]
            }
            
            if team_id not in teams:
                return jsonify({'error': 'Team not found'}), 404

            # Start each agent in the team
            started_agents = []
            for agent_name in teams[team_id]:
                try:
                    success = web_instance.agent_service.toggle_agent(agent_name, 'start')
                    if success:
                        started_agents.append(agent_name)
                except Exception as agent_error:
                    web_instance.log_message(f"Error starting agent {agent_name}: {str(agent_error)}", 'error')

            return jsonify({
                'status': 'success',
                'started_agents': started_agents,
                'team': team_id
            })

        except Exception as e:
            web_instance.log_message(f"Error starting team {team_id}: {str(e)}", 'error')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/teams/<team_id>/stop', methods=['POST'], endpoint='api_team_stop')
    @safe_operation()
    def stop_team(team_id):
        """Stop all agents in a team"""
        try:
            # Get team configuration
            teams = {
                "book_writing": ["specifications", "management", "evaluation", "chroniqueur", 
                               "documentaliste", "duplication", "redacteur", "validation"],
                "literature_review": ["specifications", "management", "evaluation", "chroniqueur",
                                    "documentaliste", "duplication", "redacteur", "validation"],
                "coding": ["specifications", "management", "evaluation", "chroniqueur",
                          "documentaliste", "duplication", "production", "testeur", "validation"]
            }
            
            if team_id not in teams:
                return jsonify({'error': 'Team not found'}), 404

            # Stop each agent in the team
            stopped_agents = []
            for agent_name in teams[team_id]:
                try:
                    success = web_instance.agent_service.toggle_agent(agent_name, 'stop')
                    if success:
                        stopped_agents.append(agent_name)
                except Exception as agent_error:
                    web_instance.log_message(f"Error stopping agent {agent_name}: {str(agent_error)}", 'error')

            return jsonify({
                'status': 'success',
                'stopped_agents': stopped_agents,
                'team': team_id
            })

        except Exception as e:
            web_instance.log_message(f"Error stopping team {team_id}: {str(e)}", 'error')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/teams/<team_id>/agents/<agent_name>/<action>', methods=['POST'], endpoint='api_team_agent_control')
    @safe_operation()
    def control_team_agent(team_id, agent_name, action):
        """Control individual agent within a team"""
        try:
            # Validate team exists
            teams = {
                "book_writing": ["specifications", "management", "evaluation", "chroniqueur", 
                               "documentaliste", "duplication", "redacteur", "validation"],
                "literature_review": ["specifications", "management", "evaluation", "chroniqueur",
                                    "documentaliste", "duplication", "redacteur", "validation"],
                "coding": ["specifications", "management", "evaluation", "chroniqueur",
                          "documentaliste", "duplication", "production", "testeur", "validation"]
            }
            
            if team_id not in teams:
                return jsonify({'error': 'Team not found'}), 404
                
            # Validate agent exists in team
            if agent_name.lower() not in [a.lower() for a in teams[team_id]]:
                return jsonify({'error': 'Agent not found in team'}), 404
                
            # Validate action
            if action not in ['start', 'stop']:
                return jsonify({'error': 'Invalid action'}), 400

            # Control agent
            success = web_instance.agent_service.toggle_agent(agent_name, action)
            
            return jsonify({
                'status': 'success' if success else 'error',
                'agent': agent_name,
                'action': action,
                'team': team_id
            })

        except Exception as e:
            web_instance.log_message(f"Error controlling team agent: {str(e)}", 'error')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/teams/<team_id>/status', methods=['GET'], endpoint='api_team_status')
    @safe_operation()
    def get_team_status(team_id):
        """Get status of all agents in a team"""
        try:
            # Get team configuration
            teams = {
                "book_writing": ["specifications", "management", "evaluation", "chroniqueur", 
                               "documentaliste", "duplication", "redacteur", "validation"],
                "literature_review": ["specifications", "management", "evaluation", "chroniqueur",
                                    "documentaliste", "duplication", "redacteur", "validation"],
                "coding": ["specifications", "management", "evaluation", "chroniqueur",
                          "documentaliste", "duplication", "production", "testeur", "validation"]
            }
            
            if team_id not in teams:
                return jsonify({'error': 'Team not found'}), 404

            # Get status for each agent
            agent_status = {}
            for agent_name in teams[team_id]:
                try:
                    status = web_instance.agent_service.get_agent_status()
                    agent_status[agent_name] = status.get(agent_name, {
                        'running': False,
                        'status': 'not_found',
                        'last_run': None,
                        'health': {
                            'is_healthy': False,
                            'consecutive_no_changes': 0
                        }
                    })
                except Exception as agent_error:
                    web_instance.log_message(f"Error getting status for agent {agent_name}: {str(agent_error)}", 'error')
                    agent_status[agent_name] = {
                        'running': False,
                        'status': 'error',
                        'error': str(agent_error)
                    }

            # Calculate team metrics
            total_agents = len(teams[team_id])
            running_agents = sum(1 for status in agent_status.values() if status.get('running', False))
            healthy_agents = sum(1 for status in agent_status.values() 
                               if status.get('health', {}).get('is_healthy', False))

            return jsonify({
                'team_id': team_id,
                'metrics': {
                    'total_agents': total_agents,
                    'running_agents': running_agents,
                    'healthy_agents': healthy_agents,
                    'health_score': (healthy_agents / total_agents) if total_agents > 0 else 0
                },
                'agents': agent_status
            })

        except Exception as e:
            web_instance.log_message(f"Error getting team status {team_id}: {str(e)}", 'error')
            return jsonify({'error': str(e)}), 500
