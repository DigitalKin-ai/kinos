"""
ModelRouter - Centralized LLM provider management and routing
"""
import os
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from anthropic import Anthropic
import openai
from utils.logger import Logger
from utils.exceptions import ServiceError

class ModelProvider(Enum):
    """Supported model providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    PERPLEXITY = "perplexity"

@dataclass
class ModelConfig:
    """Model configuration"""
    provider: ModelProvider
    model_id: str
    max_tokens: int
    temperature: float = 0.7
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

class ModelRouter:
    """Routes requests to appropriate LLM providers"""

    DEFAULT_CONFIGS = {
        "default": ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_id="claude-3-haiku-20240307",
            max_tokens=4000,
            temperature=0.7
        ),
        "fast": ModelConfig(
            provider=ModelProvider.OPENAI,
            model_id="gpt-4-0125-preview",
            max_tokens=4000,
            temperature=0.7
        ),
        "research": ModelConfig(
            provider=ModelProvider.PERPLEXITY,
            model_id="llama-3.1-sonar-large-128k-chat",
            max_tokens=4000,
            temperature=0.2
        )
    }

    def __init__(self):
        """Initialize router with API keys and configs"""
        self.logger = Logger()
        
        # Load API keys
        self.api_keys = self._load_api_keys()
        
        # Initialize clients
        self.clients = self._initialize_clients()
        
        # Load custom configurations
        self.configs = self._load_custom_configs()

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

    def _load_custom_configs(self) -> Dict[str, ModelConfig]:
        """Load custom model configurations"""
        # Start with default configs
        configs = self.DEFAULT_CONFIGS.copy()
        
        # Load custom configs from file if exists
        config_path = os.path.join("config", "model_configs.json")
        if os.path.exists(config_path):
            try:
                import json
                with open(config_path, 'r') as f:
                    custom_configs = json.load(f)
                    
                for name, config in custom_configs.items():
                    configs[name] = ModelConfig(**config)
                    
            except Exception as e:
                self.logger.log(f"Error loading custom configs: {str(e)}", 'error')
                
        return configs

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        config_name: str = "default",
        **kwargs
    ) -> Optional[str]:
        """
        Generate response using specified model configuration
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            config_name: Name of model configuration to use
            **kwargs: Additional model parameters
            
        Returns:
            Generated response text or None on error
        """
        try:
            # Get model config
            config = self.configs.get(config_name, self.DEFAULT_CONFIGS["default"])
            
            # Get appropriate client
            client = self.clients.get(config.provider.value)
            if not client:
                raise ServiceError(f"No client available for provider {config.provider.value}")
                
            # Route to appropriate provider
            if config.provider == ModelProvider.ANTHROPIC:
                response = await self._generate_anthropic(client, messages, config, **kwargs)
            elif config.provider == ModelProvider.OPENAI:
                response = await self._generate_openai(client, messages, config, **kwargs)
            elif config.provider == ModelProvider.PERPLEXITY:
                response = await self._generate_perplexity(client, messages, config, **kwargs)
            else:
                raise ValueError(f"Unsupported provider: {config.provider}")
                
            return response
            
        except Exception as e:
            self.logger.log(f"Error generating response: {str(e)}", 'error')
            return None

    async def _generate_anthropic(
        self,
        client: Anthropic,
        messages: List[Dict[str, str]],
        config: ModelConfig,
        **kwargs
    ) -> str:
        """Generate response using Anthropic's Claude"""
        response = await client.messages.create(
            model=config.model_id,
            max_tokens=config.max_tokens,
            messages=messages,
            temperature=config.temperature,
            **kwargs
        )
        return response.content[0].text

    async def _generate_openai(
        self,
        client: openai.OpenAI,
        messages: List[Dict[str, str]],
        config: ModelConfig,
        **kwargs
    ) -> str:
        """Generate response using OpenAI"""
        response = await client.chat.completions.create(
            model=config.model_id,
            messages=messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            **kwargs
        )
        return response.choices[0].message.content

    async def _generate_perplexity(
        self,
        client: Any,
        messages: List[Dict[str, str]],
        config: ModelConfig,
        **kwargs
    ) -> str:
        """Generate response using Perplexity"""
        response = await client.chat.completions.create(
            model=config.model_id,
            messages=messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            **kwargs
        )
        return response.choices[0].message.content

    def get_available_models(self) -> Dict[str, List[str]]:
        """Get list of available models per provider"""
        available = {}
        
        # Anthropic models
        if 'anthropic' in self.clients:
            available['anthropic'] = [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ]
            
        # OpenAI models    
        if 'openai' in self.clients:
            available['openai'] = [
                "gpt-4-0125-preview",
                "gpt-4-turbo-preview",
                "gpt-3.5-turbo"
            ]
            
        # Perplexity models
        if 'perplexity' in self.clients:
            available['perplexity'] = [
                "llama-3.1-sonar-large-128k-chat"
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
