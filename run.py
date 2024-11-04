from gevent import pywsgi, monkey
from geventwebsocket.handler import WebSocketHandler
from parallagon_web import ParallagonWeb
import logging
import os
from dotenv import load_dotenv

# Apply gevent monkey patching at the start
monkey.patch_all()

def get_config():
    # Load environment variables from .env file
    load_dotenv()
    
    return {
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", "your-api-key-here"),
        "openai_api_key": os.getenv("OPENAI_API_KEY", "your-api-key-here")
    }

def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    try:
        config = get_config()
        
        # Check if API keys are properly loaded
        if config["anthropic_api_key"] == "your-api-key-here":
            logger.warning("ANTHROPIC_API_KEY not found in environment variables")
        if config["openai_api_key"] == "your-api-key-here":
            logger.warning("OPENAI_API_KEY not found in environment variables")
    
        # Initialize the ParallagonWeb application
        logger.info("Initializing ParallagonWeb application...")
        app = ParallagonWeb(config)
        
        # Get the Flask app instance
        flask_app = app.get_app()
        
        logger.info("Starting Parallagon Web with gevent-websocket...")
        logger.info("Server running at http://0.0.0.0:5000")
        
        # Run with gevent-websocket
        server = pywsgi.WSGIServer(
            ('0.0.0.0', 5000), 
            flask_app,
            handler_class=WebSocketHandler
        )
        server.serve_forever()

    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise

if __name__ == "__main__":
    main()
