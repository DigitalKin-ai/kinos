import os
from datetime import datetime
from utils.path_manager import PathManager

class Logger:
    COLORS = {
        'info': 'blue',
        'success': 'green',
        'warning': 'orange',
        'error': 'red',
        'debug': 'gray',
        'redacteur': 'purple'
    }
    
    def log(self, message: str, level: str = 'info', file_path: str = None):
        """Main logging method"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] [{level.upper()}] {message}"
            
            print(formatted_message)
            
            if not file_path:
                # Use PathManager for the log path
                file_path = os.path.join(PathManager.get_logs_path(), 'agent_operations.log')
                
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"{formatted_message}\n")
                
        except Exception as e:
            print(f"Logging error: {e}")
            print(f"Original message: {message}")
            
    def __call__(self, message: str, level: str = 'info', **kwargs):
        """Alias for log method to maintain compatibility"""
        self.log(message, level=level)
