from parallagon_web import ParallagonWeb
import logging
import os
import sys
import signal
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_config():
    load_dotenv(override=True)
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    config = {
        "anthropic_api_key": anthropic_key,
        "openai_api_key": openai_key,
        "logger": logger.info
    }
    
    return config

# Create the application instance
parallagon = ParallagonWeb(get_config())
app = parallagon.get_app()  # This is the WSGI application

if __name__ == '__main__':
    if sys.platform == 'win32':
        # Windows - use waitress
        from waitress import serve
        serve(app, host='127.0.0.1', port=8000)
    else:
        # Linux/Unix - use Flask's built-in server
        app.run(host='0.0.0.0', port=8000)
