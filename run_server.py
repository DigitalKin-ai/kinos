from waitress import serve
from parallagon_web import ParallagonWeb

if __name__ == '__main__':
    config = {
        "openai_api_key": "your-api-key",  # Replace with actual key
        "anthropic_api_key": "your-api-key",  # Replace with actual key
        "logger": print
    }
    app = ParallagonWeb(config).app
    print("Starting server on http://127.0.0.1:8000")
    serve(app, host='127.0.0.1', port=8000)
