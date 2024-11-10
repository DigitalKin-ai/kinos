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
    
    def log(self, message: str, **kwargs):
        """Main logging method that handles all cases"""
        try:
            # Extract level from kwargs or use default
            level = kwargs.pop('level', 'info')
            
            # Extract file_path from kwargs
            file_path = kwargs.pop('file_path', None)
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] [{level.upper()}] {message}"
            
            print(formatted_message)
            
            if not file_path:
                file_path = os.path.join(PathManager.get_logs_path(), 'agent_operations.log')
                
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"{formatted_message}\n")
                
        except Exception as e:
            print(f"Logging error: {e}")
            print(f"Original message: {message}")
            
    def __call__(self, message: str, **kwargs):
        """Unified call method that handles all logging patterns"""
        self.log(message, **kwargs)

    def _log(self, message: str, **kwargs):
        """Alias for log method"""
        self.log(message, **kwargs)
