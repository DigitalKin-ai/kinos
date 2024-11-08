from flask import jsonify, request
from utils.decorators import safe_operation

def register_notification_routes(app, web_instance):
    @app.route('/api/notifications', methods=['GET'])
    @safe_operation()
    def get_notifications():
        notifications = web_instance.notification_service.get_notifications()
        return jsonify(notifications)

    @app.route('/api/notifications', methods=['POST'])
    @safe_operation()
    def handle_notification():
        data = request.get_json()
        success = web_instance.notification_service.handle_content_change(
            file_path=data.get('file_path'),
            content=data.get('content'),
            panel_name=data.get('panel'),
            flash=data.get('flash', False)
        )
        if not success:
            return jsonify({'error': 'Failed to handle notification'}), 500
        return jsonify({'status': 'success'})

    @app.route('/api/changes')
    @safe_operation()
    def get_changes():
        changes = web_instance.notification_service.get_notifications()
        return jsonify(changes)
