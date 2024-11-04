from flask import Flask
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
    # Force le chargement depuis le fichier .env
    load_dotenv(override=True)
    
    # Récupérer les clés
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    # Debug log pour vérifier les valeurs
    logger.info(f"Anthropic key loaded: {'Yes' if anthropic_key else 'No'}")
    logger.info(f"OpenAI key loaded: {'Yes' if openai_key else 'No'}")
    
    config = {
        "anthropic_api_key": anthropic_key,
        "openai_api_key": openai_key
    }
    
    # Validation plus stricte
    if not anthropic_key or anthropic_key == "your-api-key-here":
        logger.error("❌ ANTHROPIC_API_KEY manquante dans le fichier .env")
        raise ValueError("ANTHROPIC_API_KEY non configurée")
        
    if not openai_key or openai_key == "your-api-key-here":
        logger.error("❌ OPENAI_API_KEY manquante dans le fichier .env")
        raise ValueError("OPENAI_API_KEY non configurée")
    
    return config

def signal_handler(signum, frame, app, logger):
    logger.info("Received shutdown signal")
    app.shutdown()
    sys.exit(0)

def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, app, logger))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, app, logger))

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
        
        # Run with Flask's development server
        flask_app.run(host='0.0.0.0', port=5000, debug=True)

    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise

if __name__ == "__main__":
    main()
