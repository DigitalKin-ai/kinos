from waitress import serve
from parallagon_web import ParallagonWeb
import logging
import os

def get_config():
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
    
        # Initialize the ParallagonWeb application
        logger.info("Initializing ParallagonWeb application...")
        parallagon = ParallagonWeb(config)
        
        # Get the Flask app instance
        app = parallagon.get_app()
        
        logger.info("Starting Parallagon Web with Waitress...")
        logger.info("Server running at http://0.0.0.0:5000")
        
        # Run with Waitress with WebSocket support
        serve(app, host='0.0.0.0', port=5000, threads=4, 
              url_scheme='ws', channel_timeout=20)

    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise

if __name__ == "__main__":
    main()
