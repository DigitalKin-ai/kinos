import pytest
from kinos_web import KinOSWeb
from config import Config

@pytest.fixture
def test_config():
    """Configuration de test"""
    return {
        "ANTHROPIC_API_KEY": "test_key",
        "OPENAI_API_KEY": "test_key",
        "DEBUG": True,
        "PORT": 5000,
        "HOST": "localhost"
    }

@pytest.fixture
def app(test_config):
    """Application Flask de test"""
    app = KinOSWeb(test_config)
    return app.get_app()

@pytest.fixture
def client(app):
    """Client de test Flask"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Runner de test Flask"""
    return app.test_cli_runner()
