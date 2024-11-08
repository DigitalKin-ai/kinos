from datetime import datetime

class NotificationService:
    def __init__(self, web_instance):
        self.web_instance = web_instance
        self.notifications_queue = []
        
    def add_notification(self, message, level='info', panel=None):
        """Add a notification to the queue"""
        try:
            notification = {
                'type': level,
                'message': message,
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'panel': panel,
                'id': len(self.notifications_queue)
            }
            self.notifications_queue.append(notification)
        except Exception as e:
            self.web_instance.log_message(f"Error adding notification: {str(e)}", level='error')
            
    def get_notifications(self):
        """Get and clear notifications queue"""
        try:
            notifications = self.notifications_queue.copy()
            self.notifications_queue.clear()
            return notifications
        except Exception as e:
            self.web_instance.log_message(f"Error getting notifications: {str(e)}", level='error')
            return []
