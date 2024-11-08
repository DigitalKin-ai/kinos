import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from utils.decorators import safe_operation
from utils.exceptions import ServiceError
from services.base_service import BaseService

class NotificationService(BaseService):
    def __init__(self, web_instance):
        super().__init__(web_instance)
        self.notifications_queue = []
        self.content_cache = {}
        self.last_modified = {}
        self.last_content = {}

    @safe_operation()
    def check_content_updates(self) -> None:
        """Check for content updates in all monitored files"""
        try:
            current_content = {}
            for file_name, path in self.web_instance.file_paths.items():
                content = self.web_instance.file_manager.read_file(file_name)
                if content is not None:
                    current_content[file_name] = content

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
            self.logger.log(f"Error checking content updates: {str(e)}", level='error')
            raise ServiceError(f"Failed to check content updates: {str(e)}")

    @safe_operation()
    def handle_content_change(self, file_path: str, content: str, 
                            panel_name: str = None, flash: bool = False) -> bool:
        """Handle content change notifications"""
        try:
            self._validate_input(file_path=file_path, content=content)
            self._log_operation('handle_content_change', 
                              file_path=file_path, 
                              panel_name=panel_name,
                              flash=flash)
            
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
                
            return True
            
        except Exception as e:
            return self._handle_error('handle_content_change', e, False)

    @safe_operation()
    def get_notifications(self) -> List[Dict[str, Any]]:
        """Get and clear pending notifications"""
        try:
            self._log_operation('get_notifications')
            current_time = datetime.now()
            
            # Filter notifications from last 3 seconds
            recent_notifications = []
            for n in self.notifications_queue:
                try:
                    notif_time = datetime.strptime(n['timestamp'], "%H:%M:%S")
                    notif_datetime = current_time.replace(
                        hour=notif_time.hour,
                        minute=notif_time.minute,
                        second=notif_time.second
                    )
                    
                    if (current_time - notif_datetime).total_seconds() <= 3:
                        recent_notifications.append(n)
                except ValueError as e:
                    self.logger.log(f"Invalid timestamp format in notification: {e}", level='error')
                    continue

            # Clear the queue after filtering
            self.notifications_queue.clear()
            
            return recent_notifications
        except Exception as e:
            return self._handle_error('get_notifications', e, [])
            
    def cleanup(self):
        """Cleanup notification service resources"""
        try:
            self._log_operation('cleanup')
            self.notifications_queue.clear()
            self.content_cache.clear()
            self.last_modified.clear()
            self.last_content.clear()
        except Exception as e:
            self._handle_error('cleanup', e)
