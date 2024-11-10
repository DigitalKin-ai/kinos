import os
import time
from datetime import datetime
import traceback
from pathlib import Path
import fnmatch
from flask import jsonify, request
from utils.decorators import safe_operation
from utils.path_manager import PathManager
from utils.exceptions import ResourceNotFoundError
from utils.error_handler import ErrorHandler



def should_ignore_file(file_path: str, ignore_patterns: list, web_instance) -> bool:
    """Check if file should be ignored based on gitignore/aiderignore patterns"""
    # Convert path to forward slashes for consistent pattern matching
    file_path = str(Path(file_path)).replace('\\', '/')
    
    for pattern in ignore_patterns:
        # Handle directory patterns ending with /
        if pattern.endswith('/'):
            if fnmatch.fnmatch(file_path + '/', pattern):
                return True
        # Handle regular patterns
        if fnmatch.fnmatch(file_path, pattern):
            return True
    return False

def load_ignore_patterns(mission_dir: str, web_instance) -> list:
    """Load patterns from .gitignore and .aiderignore files"""
    ignore_patterns = []
    ignore_files = ['.gitignore', '.aiderignore']
    
    for ignore_file in ignore_files:
        file_path = os.path.join(mission_dir, ignore_file)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Skip empty lines and comments
                        if line and not line.startswith('#'):
                            # Convert Windows paths to forward slashes
                            line = line.replace('\\', '/')
                            ignore_patterns.append(line)
            except Exception as e:
                web_instance.logger.log(f"Error reading {ignore_file}: {str(e)}", 'error')
                
    return ignore_patterns

def _validate_mission(mission_id: int, web_instance) -> dict:
    """Centralized mission validation"""
    mission = web_instance.mission_service.get_mission(mission_id)
    if not mission:
        raise ResourceNotFoundError(f"Mission {mission_id} not found")
    return mission

def _validate_mission(mission_id: int, web_instance) -> dict:
    """Centralized mission validation"""
    mission = web_instance.mission_service.get_mission(mission_id)
    if not mission:
        raise ResourceNotFoundError(f"Mission {mission_id} not found")
    return mission

def register_mission_routes(app, web_instance):
    """Register all mission-related routes"""
    
    @app.route('/api/paths/mission/<mission_name>', endpoint='api_mission_path_by_name')
    @safe_operation()
    def get_mission_path_by_name(mission_name):
        return jsonify({
            'path': PathManager.get_mission_path(mission_name)
        })

    @app.route('/api/missions/<int:mission_id>/path', endpoint='api_mission_path')
    @safe_operation()
    def get_mission_path(mission_id):
        mission = web_instance.mission_service.get_mission(mission_id)
        if not mission:
            return jsonify({'error': 'Mission not found'}), 404
        return jsonify({
            'path': PathManager.get_mission_path(mission['name'])
        })

    @app.route('/api/missions', methods=['GET'], endpoint='api_missions_list')
    @safe_operation()
    def get_missions():
        missions = web_instance.mission_service.get_all_missions()
        return jsonify(missions)

    @app.route('/api/missions/<int:mission_id>/files', endpoint='api_mission_files')
    @safe_operation()
    @web_instance.limiter.limit("200 per minute")
    def get_mission_files(mission_id):
        """Get all files in mission directory respecting ignore patterns"""
        try:
            # Log début de la requête
            web_instance.logger.log(f"Getting files for mission {mission_id}", 'debug')
            
            # Get mission
            mission = web_instance.mission_service.get_mission(mission_id)
            if not mission:
                web_instance.logger.log(f"Mission {mission_id} not found", 'error')
                return jsonify({'error': 'Mission not found'}), 404

            # Log mission trouvée
            web_instance.logger.log(f"Found mission: {mission['name']}", 'debug')

            # Get mission path using PathManager
            mission_dir = PathManager.get_mission_path(mission['name'])
            web_instance.logger.log(f"Mission directory: {mission_dir}", 'debug')

            # Vérifier que le dossier existe
            if not os.path.exists(mission_dir):
                web_instance.logger.log(f"Mission directory not found: {mission_dir}", 'error')
                return jsonify({'error': 'Mission directory not found'}), 404

            # Load ignore patterns
            ignore_patterns = load_ignore_patterns(mission_dir, web_instance)
            web_instance.logger.log(f"Loaded ignore patterns: {ignore_patterns}", 'debug')

            files = []
            try:
                for root, _, filenames in os.walk(mission_dir):
                    # Get path relative to mission directory for pattern matching
                    rel_root = os.path.relpath(root, mission_dir)
                    
                    for filename in filenames:
                        if filename.endswith(('.md', '.txt', '.py', '.js', '.json', '.yaml', '.yml')):
                            try:
                                # Get relative path for pattern matching
                                rel_path = os.path.join(rel_root, filename)
                                rel_path = rel_path.replace('\\', '/')
                                
                                # Skip if file matches ignore patterns
                                if should_ignore_file(rel_path, ignore_patterns, web_instance):
                                    continue

                                full_path = os.path.join(root, filename)
                                file_info = {
                                    'name': filename,
                                    'path': rel_path,
                                    'relativePath': rel_path,
                                    'size': os.path.getsize(full_path),
                                    'modified': os.path.getmtime(full_path)
                                }
                                files.append(file_info)
                                #web_instance.logger.log(f"Added file: {rel_path}", 'debug')
                                
                            except (OSError, IOError) as e:
                                web_instance.logger.log(f"Error processing file {filename}: {str(e)}", 'error')
                                continue

                # Sort files by path
                files.sort(key=lambda x: x['path'])
                
                web_instance.logger.log(f"Found {len(files)} files in mission {mission['name']}", 'info')
                return jsonify(files)

            except Exception as e:
                web_instance.logger.log(f"Error listing files: {str(e)}", 'error')
                return jsonify({'error': f'Error listing files: {str(e)}'}), 500

        except Exception as e:
            web_instance.logger.log(f"Unexpected error in get_mission_files: {str(e)}", 'error')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/missions/<int:mission_id>/select', methods=['POST'], endpoint='api_mission_select')
    @safe_operation()
    def select_mission(mission_id):
        try:
            web_instance.logger.log(f"Sélection de mission demandée: {mission_id}", 'info')
            
            # Validation de la mission
            mission = web_instance.mission_service.get_mission(mission_id)
            if not mission:
                web_instance.logger.log(f"Mission {mission_id} non trouvée", 'error')
                return jsonify({
                    'error': 'Mission not found',
                    'details': f'No mission with id {mission_id}'
                }), 404

            # Mise à jour de la mission courante
            try:
                web_instance.file_manager.current_mission = mission['name']
                web_instance.logger.log(f"Mission courante mise à jour: {mission['name']}", 'info')
            except Exception as e:
                web_instance.logger.log(f"Erreur mise à jour mission: {str(e)}", 'error')
                return jsonify({
                    'error': 'Failed to update current mission',
                    'details': str(e)
                }), 500

            # Réinitialisation des agents
            try:
                web_instance.agent_service.init_agents({
                    "anthropic_api_key": web_instance.config.get("anthropic_api_key"),
                    "openai_api_key": web_instance.config.get("openai_api_key")
                })
                web_instance.logger.log("Agents réinitialisés avec succès", 'success')
            except Exception as e:
                web_instance.logger.log(f"Erreur initialisation agents: {str(e)}", 'error')
                return jsonify({
                    'error': 'Failed to initialize agents',
                    'details': str(e)
                }), 500

            return jsonify({
                'status': 'success',
                'mission': mission,
                'selected_at': datetime.now().isoformat()
            })

        except Exception as e:
            web_instance.logger.log(f"Erreur inattendue: {str(e)}", 'error')
            return jsonify({
                'error': 'Unexpected error',
                'details': str(e)
            }), 500

    @app.route('/api/missions/<int:mission_id>/reset', methods=['POST'], endpoint='api_mission_reset')
    @safe_operation()
    def reset_mission_files(mission_id):
        success = web_instance.mission_service.reset_mission_files(mission_id)
        if not success:
            return jsonify({'error': 'Failed to reset files'}), 500
        return jsonify({'status': 'success'})

    @app.route('/api/missions/<int:mission_id>/teams', methods=['GET'], endpoint='api_mission_teams')
    @safe_operation()
    def get_mission_teams(mission_id):
        """Get teams available for a mission"""
        try:
            # Validate mission exists
            mission = _validate_mission(mission_id, web_instance)
            
            # Get teams from team service
            teams = web_instance.team_service.get_teams_for_mission(mission_id)
            
            return jsonify(teams)
            
        except Exception as e:
            web_instance.logger.log(f"Error getting teams for mission {mission_id}: {str(e)}", 'error')
            return ErrorHandler.handle_error(e)

    @app.route('/api/missions/<int:mission_id>/files/<path:file_path>', methods=['GET'], endpoint='api_mission_file_content')
    @safe_operation()
    def get_mission_file_content(mission_id, file_path):
        """Get content of a specific file in mission directory"""
        try:
            # Get mission
            mission = web_instance.mission_service.get_mission(mission_id)
            if not mission:
                return jsonify({'error': 'Mission not found'}), 404

            # Get mission path using PathManager
            mission_dir = PathManager.get_mission_path(mission['name'])
            
            # Sécuriser le chemin du fichier
            safe_path = os.path.normpath(file_path)
            if safe_path.startswith('..'):
                return jsonify({'error': 'Invalid file path'}), 400

            # Get mission path using PathManager
            mission_dir = PathManager.get_mission_path(mission['name'])
            
            # Construire le chemin complet avec le dossier de mission
            full_path = os.path.join(mission_dir, safe_path)
            
            # Log pour debug
            web_instance.logger.log(f"Accessing file: {full_path}", 'debug')
            
            # Vérifier que le fichier existe
            if not os.path.exists(full_path):
                return jsonify({'error': f'File not found: {full_path}'}), 404

            # Vérifier l'extension
            ext = os.path.splitext(full_path)[1].lower()
            if ext not in {'.md', '.txt', '.py', '.js', '.json', '.yaml', '.yml'}:
                return jsonify({'error': 'Unsupported file type'}), 400

            # Lire le contenu du fichier
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return content, 200, {'Content-Type': 'text/plain'}

        except Exception as e:
            return ErrorHandler.handle_error(e)
