from flask import jsonify, request
from datetime import datetime

def register_notification_routes(app, web_instance):
    @app.route('/api/notifications', methods=['GET', 'POST'])
    @web_instance.limiter.limit("500 per minute")
    def handle_notifications():
        if request.method == 'GET':
            return web_instance.get_notifications()
        else:
            return web_instance.handle_notification()

    @app.route('/api/changes')
    def get_changes():
        return web_instance.get_changes()
