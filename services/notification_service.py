import time
from datetime import datetime

class NotificationService:
    def __init__(self, web_instance):
        self.web_instance = web_instance
        self.notifications_queue = []
        self.content_cache = {}
        self.last_modified = {}
        
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

    def check_content_updates(self):
        """Check for content updates"""
        try:
            current_content = {}
            for file_name, path in self.web_instance.file_paths.items():
                content = self.web_instance.file_manager.read_file(file_name)
                if content is not None:
                    current_content[file_name] = content

            if not hasattr(self, 'last_content'):
                self.last_content = {}

            for file_name, content in current_content.items():
                if content is None:
                    continue
                    
                if (file_name not in self.last_content or 
                    content != self.last_content[file_name]):
                    self.handle_content_change(
                        file_name, 
                        content,
                        panel_name=file_name.split('.')[0].capitalize()
                    )
                    self.last_content[file_name] = content

        except Exception as e:
            self.web_instance.log_message(f"Error checking content updates: {str(e)}", level='error')

    def handle_content_change(self, file_path: str, content: str, panel_name: str = None, flash: bool = False):
        """Handle content change notifications"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if not panel_name:
                panel_name = os.path.splitext(os.path.basename(file_path))[0].capitalize()
            
            notification = {
                'type': 'info',
                'message': f'Content updated in {panel_name}',
                'timestamp': timestamp,
                'panel': panel_name,
                'status': os.path.basename(file_path),
                'operation': 'flash_tab' if flash else 'update',
                'id': len(self.notifications_queue),
                'flash': flash
            }
            
            self.notifications_queue.append(notification)
            
            if content and content.strip():
                self.content_cache[file_path] = content
                self.last_modified[file_path] = time.time()
                self.web_instance.log_message(f"Content cache updated for {panel_name}", level='debug')
                
            return True
            
        except Exception as e:
            self.web_instance.log_message(f"Error handling content change: {str(e)}", level='error')
            return False
