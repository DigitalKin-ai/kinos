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
    
    # Debug log pour vérifier les valeurs (ne pas logger les clés complètes en prod)
    logger.info(f"Anthropic key loaded: {'Yes' if anthropic_key else 'No'}")
    logger.info(f"OpenAI key loaded: {'Yes' if openai_key else 'No'}")
    
    config = {
        "anthropic_api_key": anthropic_key,
        "openai_api_key": openai_key,
        "logger": logger.info
    }
    
    # Validation plus stricte
    if not anthropic_key or not anthropic_key.startswith("sk-"):
        logger.error("❌ ANTHROPIC_API_KEY manquante ou invalide dans le fichier .env")
        raise ValueError("ANTHROPIC_API_KEY non configurée correctement")
        
    if not openai_key or not openai_key.startswith("sk-"):
        logger.error("❌ OPENAI_API_KEY manquante ou invalide dans le fichier .env")
        raise ValueError("OPENAI_API_KEY non configurée correctement")
    
    return config

def signal_handler(signum, frame, app, logger):
    logger.info("Received shutdown signal")
    sys.exit(0)

if __name__ == '__main__':
    try:
        config = get_config()
        app = ParallagonWeb(config).app
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, app, logger))
        signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, app, logger))
        
        # Choose server based on platform
        if sys.platform == 'win32':
            # Windows - use waitress
            from waitress import serve
            logger.info("Starting waitress server on http://127.0.0.1:8000")
            serve(app, host='127.0.0.1', port=8000)
        else:
            # Linux/Unix - use Flask's built-in server
            logger.info("Starting Flask server on http://0.0.0.0:8000")
            app.run(host='0.0.0.0', port=8000)
            
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise
