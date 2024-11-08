import os
from flask import jsonify, request
from utils.decorators import safe_operation

def register_mission_routes(app, web_instance):
    @app.route('/api/missions', methods=['GET'])
    @safe_operation()
    def get_missions():
        missions = web_instance.mission_service.get_all_missions()
        return jsonify(missions)

    @app.route('/api/missions', methods=['POST'])
    @safe_operation()
    def create_mission():
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Name is required'}), 400
            
        mission = web_instance.mission_service.create_mission(
            name=data['name'],
            description=data.get('description')
        )
        return jsonify(mission), 201

    @app.route('/api/missions/<int:mission_id>', methods=['GET'])
    @safe_operation()
    def get_mission(mission_id):
        mission = web_instance.mission_service.get_mission(mission_id)
        if not mission:
            return jsonify({'error': 'Mission not found'}), 404
        return jsonify(mission)

    @app.route('/api/missions/<int:mission_id>/content', methods=['GET'])
    @safe_operation()
    def get_mission_content(mission_id):
        content = web_instance.mission_service.get_mission_content(mission_id)
        if not content:
            return jsonify({'error': 'Content not found'}), 404
        return jsonify(content)

    @app.route('/api/missions/<int:mission_id>/test-data', methods=['POST'])
    @safe_operation()
    def load_test_data(mission_id):
        success = web_instance.mission_service.load_test_data(mission_id)
        if not success:
            return jsonify({'error': 'Failed to load test data'}), 500
        return jsonify({'status': 'success'})

    @app.route('/api/missions/<int:mission_id>/files')
    @safe_operation()
    def get_mission_files(mission_id):
        """Get all files in mission directory"""
        try:
            # Log the request
            web_instance.logger.log(f"Getting files for mission {mission_id}", level='debug')
            
            # Get mission
            mission = web_instance.mission_service.get_mission(mission_id)
            if not mission:
                web_instance.logger.log(f"Mission {mission_id} not found", level='error')
                return jsonify({'error': 'Mission not found'}), 404

            # Log mission info
            web_instance.logger.log(f"Found mission: {mission['name']}", level='debug')
            
            # Get mission directory path
            mission_dir = os.path.abspath(os.path.join("missions", mission['name']))
            web_instance.logger.log(f"Mission directory: {mission_dir}", level='debug')
            
            # Check if directory exists
            if not os.path.exists(mission_dir):
                web_instance.logger.log(f"Mission directory not found: {mission_dir}", level='error')
                # Create directory if it doesn't exist
                try:
                    os.makedirs(mission_dir, exist_ok=True)
                    web_instance.logger.log(f"Created mission directory: {mission_dir}", level='info')
                except Exception as e:
                    web_instance.logger.log(f"Failed to create mission directory: {str(e)}", level='error')
                    return jsonify({'error': 'Failed to create mission directory'}), 500

            # Ensure required files exist
            required_files = ["demande.md", "specifications.md", "management.md", 
                            "production.md", "evaluation.md", "suivi.md"]
            for filename in required_files:
                file_path = os.path.join(mission_dir, filename)
                if not os.path.exists(file_path):
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write("")  # Create empty file
                        web_instance.logger.log(f"Created file: {filename}", level='info')
                    except Exception as e:
                        web_instance.logger.log(f"Failed to create {filename}: {str(e)}", level='error')
                        continue

            # Get all files
            files = []
            try:
                for root, _, filenames in os.walk(mission_dir):
                    for filename in filenames:
                        if filename.endswith(('.md', '.txt', '.py', '.js', '.json', '.yaml', '.yml')):
                            full_path = os.path.join(root, filename)
                            relative_path = os.path.relpath(full_path, mission_dir)
                            
                            files.append({
                                'name': filename,
                                'path': relative_path,
                                'size': os.path.getsize(full_path),
                                'modified': os.path.getmtime(full_path)
                            })
                
                web_instance.logger.log(f"Found {len(files)} files", level='debug')
                return jsonify(files)
                
            except Exception as e:
                web_instance.logger.log(f"Error scanning files: {str(e)}", level='error')
                return jsonify({'error': f'Error scanning files: {str(e)}'}), 500

        except Exception as e:
            web_instance.logger.log(f"Unexpected error: {str(e)}", level='error')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/missions/<int:mission_id>/reset', methods=['POST'])
    @safe_operation()
    def reset_mission_files(mission_id):
        success = web_instance.mission_service.reset_mission_files(mission_id)
        if not success:
            return jsonify({'error': 'Failed to reset files'}), 500
        return jsonify({'status': 'success'})
