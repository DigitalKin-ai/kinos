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
    
    @staticmethod
    def log(message: str, level: str = 'info', file_path: str = None):
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] [{level.upper()}] {message}"
            
            print(formatted_message)
            
            if not file_path:
                # Use PathManager for the log path
                from utils.path_manager import PathManager
                file_path = os.path.join(PathManager.get_logs_path(), 'agent_operations.log')
                
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"{formatted_message}\n")
                
        except Exception as e:
            print(f"Logging error: {e}")
            print(f"Original message: {message}")
