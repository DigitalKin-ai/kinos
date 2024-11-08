from flask import jsonify, request
import os

def register_mission_routes(app, web_instance):
    @app.route('/api/missions', methods=['GET', 'POST'])
    def handle_missions():
        if request.method == 'GET':
            return web_instance.get_all_missions()
        else:
            return web_instance.create_mission()

    @app.route('/api/missions/<int:mission_id>', methods=['GET', 'PUT'])
    def handle_mission(mission_id):
        if request.method == 'GET':
            return web_instance.get_mission(mission_id)
        else:
            return web_instance.update_mission(mission_id)

    @app.route('/api/missions/<int:mission_id>/content', methods=['GET'])
    def get_mission_content(mission_id):
        return web_instance.get_mission_content(mission_id)

    @app.route('/api/missions/<int:mission_id>/files/<path:file_path>')
    def get_mission_file_content(mission_id, file_path):
        return web_instance.get_mission_file_content(mission_id, file_path)
