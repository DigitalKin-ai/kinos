from flask import jsonify, request
import os
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

    @app.route('/api/missions/<int:mission_id>/reset', methods=['POST'])
    @safe_operation()
    def reset_mission_files(mission_id):
        success = web_instance.mission_service.reset_mission_files(mission_id)
        if not success:
            return jsonify({'error': 'Failed to reset files'}), 500
        return jsonify({'status': 'success'})
