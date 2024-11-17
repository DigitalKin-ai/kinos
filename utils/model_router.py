"""
ModelRouter - Centralized LLM provider management and routing
"""
import os
from typing import Dict, Any, Optional, List
from enum import Enum
from anthropic import Anthropic
import openai
from utils.logger import Logger
from utils.exceptions import ServiceError

class ModelProvider(Enum):
    """Supported model providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    PERPLEXITY = "perplexity"

class ModelConfig:
    """Model configuration"""
    def __init__(self, provider: ModelProvider, model_id: str, max_tokens: int = 4000, temperature: float = 0.7):
        self.provider = provider
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature

class ModelRouter:
    """Routes requests to appropriate LLM providers"""

    def __init__(self):
        """Initialize router with API keys"""
        self.logger = Logger()
        self.api_keys = self._load_api_keys()
        self.clients = self._initialize_clients()
        self.current_model = None  # Start with no model selected
        self.current_provider = None  # Start with no provider selected

    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment"""
        keys = {}
        
        # Anthropic
        if anthropic_key := os.getenv('ANTHROPIC_API_KEY'):
            keys['anthropic'] = anthropic_key
            
        # OpenAI    
        if openai_key := os.getenv('OPENAI_API_KEY'):
            keys['openai'] = openai_key
            
        # Perplexity
        if perplexity_key := os.getenv('PERPLEXITY_API_KEY'):
            keys['perplexity'] = perplexity_key
            
        return keys

    def _initialize_clients(self) -> Dict[str, Any]:
        """Initialize API clients"""
        clients = {}
        
        # Anthropic
        if 'anthropic' in self.api_keys:
            try:
                clients['anthropic'] = Anthropic(api_key=self.api_keys['anthropic'])
            except Exception as e:
                self.logger.log(f"Error initializing Anthropic client: {str(e)}", 'error')
                
        # OpenAI
        if 'openai' in self.api_keys:
            try:
                clients['openai'] = openai.OpenAI(api_key=self.api_keys['openai'])
            except Exception as e:
                self.logger.log(f"Error initializing OpenAI client: {str(e)}", 'error')
                
        return clients

    def set_model(self, model_name: str) -> bool:
        """Set current model if valid"""
        available = self.get_available_models()
        
        for provider, models in available.items():
            if model_name in models:
                self.current_model = model_name
                self.current_provider = ModelProvider(provider)
                self.logger.log(f"Using model: {model_name} from {provider}", 'info')
                return True
                
        self.logger.log(f"Model {model_name} not found in available models", 'error')
        return False

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """Generate response using current model"""
        try:
            if not self.current_model or not self.current_provider:
                raise ServiceError("No model selected. Call set_model() first.")

            client = self.clients.get(self.current_provider.value)
            if not client:
                raise ServiceError(f"No client available for provider {self.current_provider.value}")

            # Only handle OpenAI case since we removed Anthropic
            if self.current_provider == ModelProvider.OPENAI:
                if system:
                    messages = [{"role": "system", "content": system}] + messages
                response = await self._generate_openai(client, messages, None, **kwargs)
            else:
                raise ValueError(f"Unsupported provider: {self.current_provider}")

            return response

        except Exception as e:
            self.logger.log(f"Error generating response: {str(e)}", 'error')
            return None

    def _generate_anthropic(
        self,
        client: Anthropic,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate response using Anthropic's Claude"""
        response = client.messages.create(
            model=self.current_model,
            messages=messages,
            system=system,  # Pass system as top-level parameter
            max_tokens=kwargs.get('max_tokens', 4000),
            temperature=kwargs.get('temperature', 0.3)
        )
        return response.content[0].text

    async def _generate_openai(
        self,
        client: openai.OpenAI,
        messages: List[Dict[str, str]], 
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate response using OpenAI"""
        if system:
            messages = [{"role": "system", "content": system}] + messages
        
        # Use synchronous create as OpenAI handles async internally
        response = client.chat.completions.create(
            model=self.current_model,
            messages=messages,
            max_tokens=kwargs.get('max_tokens', 4000),
            temperature=kwargs.get('temperature', 0.7)
        )
        return response.choices[0].message.content

    async def _generate_perplexity(
        self,
        client: Any,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate response using Perplexity"""
        if system:
            messages = [{"role": "system", "content": system}] + messages
            
        response = await client.chat.completions.create(
            model=self.current_model,
            messages=messages,
            max_tokens=kwargs.get('max_tokens', 4000),
            temperature=kwargs.get('temperature', 0.3)
        )
        return response.choices[0].message.content

    def get_current_tokenizer(self):
        """Get tokenizer for current model"""
        try:
            client = self.clients.get(self.current_provider.value)
            if not client:
                raise ServiceError(f"No client available for provider {self.current_provider.value}")
                
            return client
            
        except Exception as e:
            self.logger.log(f"Error getting tokenizer: {str(e)}", 'error')
            return None

    def get_available_models(self) -> Dict[str, List[str]]:
        """Get list of available models per provider"""
        available = {}
        
        # Anthropic models
        if 'anthropic' in self.clients:
            available['anthropic'] = [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022"
            ]
                
        # OpenAI models    
        if 'openai' in self.clients:
            available['openai'] = [
                "gpt-4o",
                "gpt-4o-mini"
            ]
            
        return available

    def validate_config(self, config: ModelConfig) -> bool:
        """Validate model configuration"""
        try:
            # Check provider availability
            if config.provider.value not in self.clients:
                return False
                
            # Check if model exists for provider
            available = self.get_available_models()
            if config.model_id not in available.get(config.provider.value, []):
                return False
                
            # Validate parameters
            if not 0 <= config.temperature <= 1:
                return False
                
            if config.max_tokens < 1:
                return False
                
            return True
            
        except Exception:
            return False
