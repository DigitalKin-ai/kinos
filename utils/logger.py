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
    
    def log(self, message: str, level: str = 'info', **kwargs):
        """Main logging method that handles all cases"""
        try:
            # Normalize level handling - remove from kwargs if present
            if 'level' in kwargs:
                level = kwargs.pop('level')
                
            # Extract file_path from kwargs if present
            file_path = kwargs.get('file_path')
            
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
        """Unified call method that handles all logging patterns"""
        # Ensure level is not duplicated
        if 'level' in kwargs:
            kwargs.pop('level')
        self.log(message, level=level, **kwargs)

    def _log(self, message: str, level: str = 'info', **kwargs):
        """Alias for log method with normalized parameters"""
        # Ensure level is not duplicated
        if 'level' in kwargs:
            kwargs.pop('level')
        self.log(message, level=level, **kwargs)
