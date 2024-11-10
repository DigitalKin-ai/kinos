import os
from pathlib import Path
import fnmatch
from flask import jsonify, request
from utils.decorators import safe_operation



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
                web_instance.logger.log(f"Error reading {ignore_file}: {str(e)}", level='error')
                
    return ignore_patterns

def register_mission_routes(app, web_instance):
    """Register all mission-related routes"""
    
    @app.route('/api/missions', methods=['GET'])
    @safe_operation()
    def get_missions():
        missions = web_instance.mission_service.get_all_missions()
        return jsonify(missions)

    @app.route('/api/missions/<int:mission_id>/files')
    @safe_operation()
    @web_instance.limiter.limit("200 per minute")
    def get_mission_files(mission_id):
        """Get all files in mission directory respecting ignore patterns"""
        try:
            # Log début de la requête
            web_instance.logger.log(f"Getting files for mission {mission_id}", level='debug')
            
            # Get mission
            mission = web_instance.mission_service.get_mission(mission_id)
            if not mission:
                web_instance.logger.log(f"Mission {mission_id} not found", level='error')
                return jsonify({'error': 'Mission not found'}), 404

            # Log mission trouvée
            web_instance.logger.log(f"Found mission: {mission['name']}", level='debug')

            # Build mission path with normalized name
            normalized_name = web_instance.mission_service._normalize_mission_name(mission['name'])
            mission_dir = os.path.join("missions", normalized_name)
            web_instance.logger.log(f"Mission directory: {mission_dir}", level='debug')

            # Vérifier que le dossier existe
            if not os.path.exists(mission_dir):
                web_instance.logger.log(f"Mission directory not found: {mission_dir}", level='error')
                return jsonify({'error': 'Mission directory not found'}), 404

            # Load ignore patterns
            ignore_patterns = load_ignore_patterns(mission_dir, web_instance)
            web_instance.logger.log(f"Loaded ignore patterns: {ignore_patterns}", level='debug')

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
                                #web_instance.logger.log(f"Added file: {rel_path}", level='debug')
                                
                            except (OSError, IOError) as e:
                                web_instance.logger.log(f"Error processing file {filename}: {str(e)}", level='error')
                                continue

                # Sort files by path
                files.sort(key=lambda x: x['path'])
                
                web_instance.logger.log(f"Found {len(files)} files in mission {mission['name']}", level='info')
                return jsonify(files)

            except Exception as e:
                web_instance.logger.log(f"Error listing files: {str(e)}", level='error')
                return jsonify({'error': f'Error listing files: {str(e)}'}), 500

        except Exception as e:
            web_instance.logger.log(f"Unexpected error in get_mission_files: {str(e)}", level='error')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/missions/<int:mission_id>/select', methods=['POST'])
    @safe_operation()
    def select_mission(mission_id):
        try:
            # Get mission
            mission = web_instance.mission_service.get_mission(mission_id)
            if not mission:
                web_instance.logger.log(f"Mission {mission_id} not found", level='error')
                return jsonify({'error': 'Mission not found'}), 404

            # Verify mission directory exists
            mission_dir = os.path.join("missions", mission['name'])
            if not os.path.exists(mission_dir):
                web_instance.logger.log(f"Mission directory not found: {mission_dir}", level='error')
                return jsonify({'error': 'Mission directory not found'}), 404

            # Stop all agents before changing mission
            web_instance.agent_service.stop_all_agents()
            
            # Update current mission in FileManager
            try:
                web_instance.file_manager.current_mission = mission['name']
            except Exception as e:
                web_instance.logger.log(f"Failed to update FileManager mission: {str(e)}", level='error')
                return jsonify({'error': 'Failed to update current mission'}), 500

            web_instance.logger.log(f"Successfully selected mission: {mission['name']}", level='success')
            
            return jsonify(mission)
            
        except Exception as e:
            web_instance.logger.log(f"Error selecting mission {mission_id}: {str(e)}", level='error')
            return jsonify({'error': f"Failed to select mission: {str(e)}"}), 500

    @app.route('/api/missions/<int:mission_id>/reset', methods=['POST'])
    @safe_operation()
    def reset_mission_files(mission_id):
        success = web_instance.mission_service.reset_mission_files(mission_id)
        if not success:
            return jsonify({'error': 'Failed to reset files'}), 500
        return jsonify({'status': 'success'})

    @app.route('/api/missions/<int:mission_id>/files/<path:file_path>', methods=['GET'])
    @safe_operation()
    def get_mission_file_content(mission_id, file_path):
        """Get content of a specific file in mission directory"""
        try:
            # Get mission
            mission = web_instance.mission_service.get_mission(mission_id)
            if not mission:
                return jsonify({'error': 'Mission not found'}), 404

            # Construire le chemin complet en incluant le nom de la mission
            mission_dir = os.path.join("missions", mission['name'])
            
            # Sécuriser le chemin du fichier
            safe_path = os.path.normpath(file_path)
            if safe_path.startswith('..'):
                return jsonify({'error': 'Invalid file path'}), 400

            # Construire le chemin complet avec le dossier de mission
            full_path = os.path.join(mission_dir, safe_path)
            
            # Log pour debug
            web_instance.logger.log(f"Accessing file: {full_path}", level='debug')
            
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
            web_instance.logger.log(f"Error reading file content: {str(e)}", level='error')
            return jsonify({'error': str(e)}), 500
