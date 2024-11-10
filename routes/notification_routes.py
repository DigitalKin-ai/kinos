from flask import jsonify, request
from utils.decorators import safe_operation

def register_notification_routes(app, web_instance):
    @app.route('/api/notifications', methods=['GET'], endpoint='api_notifications_get')
    @safe_operation()
    def get_notifications():
        notifications = web_instance.notification_service.get_notifications()
        return jsonify(notifications)

    @app.route('/api/notifications', methods=['POST'], endpoint='api_notifications_post')
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

