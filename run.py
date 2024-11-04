from waitress import serve
from parallagon_web import ParallagonWeb

def main():
    config = {
        "anthropic_api_key": "your-api-key-here",
        "openai_api_key": "your-api-key-here"
    }
    
    # Initialize the ParallagonWeb application
    parallagon = ParallagonWeb(config)
    
    # Get the Flask app instance
    app = parallagon.get_app()
    
    print("Starting Parallagon Web with Waitress...")
    print("Server running at http://0.0.0.0:5000")
    
    # Run with Waitress
    serve(app, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()
