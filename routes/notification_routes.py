from datetime import datetime
import time
from flask import jsonify, request
from utils.decorators import safe_operation

def register_notification_routes(app, web_instance):
    def _format_notification(message: str, panel: str, flash: bool = False) -> dict:
        """Format notification with standard fields"""
        return {
            'type': 'info',
            'message': message,
            'panel': panel,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'flash': flash,
            'id': len(web_instance.notification_service.notifications_queue)
        }

    def _handle_notification(data: dict) -> bool:
        """Centralized notification handling"""
        try:
            # Validate required fields
            required_fields = ['file_path', 'content', 'panel', 'message']
            if not all(field in data for field in required_fields):
                missing = [f for f in required_fields if f not in data]
                web_instance.logger.log(f"Missing required fields: {missing}", 'error')
                return False
                
            # Format notification
            notification = _format_notification(
                message=data['message'],
                panel=data['panel'],
                flash=data.get('flash', True)
            )
            
            # Add to queue
            web_instance.notification_service.notifications_queue.append(notification)
            
            # Update cache if needed
            if data['content'].strip():
                web_instance.notification_service.content_cache[data['file_path']] = data['content']
                web_instance.notification_service.last_modified[data['file_path']] = time.time()
                
            return True
            
        except Exception as e:
            web_instance.logger.log(f"Error handling notification: {str(e)}", 'error')
            return False

    @app.route('/api/notifications', methods=['GET'], endpoint='api_notifications_get')
    @safe_operation()
    def get_notifications():
        notifications = web_instance.notification_service.get_notifications()
        return jsonify(notifications)

    @app.route('/api/notifications', methods=['POST'], endpoint='api_notifications_post')
    @safe_operation()
    def handle_notification():
        data = request.get_json()
        success = _handle_notification(data)
        if not success:
            return jsonify({'error': 'Failed to handle notification'}), 500
        return jsonify({'status': 'success'})

