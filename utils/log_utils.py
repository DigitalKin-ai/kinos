from datetime import datetime

def log_message(message: str, level: str = 'info') -> None:
    """Basic logging function for internal use"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level.upper()}] {message}")
