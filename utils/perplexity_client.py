"""
PerplexityClient - Client for interacting with Perplexity API
"""
import os
import json
import requests
from typing import Dict, Any, Optional
from utils.logger import Logger
from dotenv import load_dotenv

class PerplexityClient:
    """Client for making Perplexity API requests"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize client with API key"""
        # Load environment variables from .env file
        load_dotenv()
        
        self.api_key = api_key or os.environ.get('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError("No Perplexity API key found in .env file or environment variables")
            
        self.logger = Logger()
        self.base_url = "https://api.perplexity.ai/v1"
        
    def execute_query(self, query: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Execute a query against Perplexity API
        
        Args:
            query: Query string
            **kwargs: Additional query parameters
            
        Returns:
            Query results or None on error
        """
        try:
            if not self.api_key:
                raise ValueError("No API key provided")
                
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare request data according to API spec
            data = {
                "model": "llama-3.1-sonar-small-128k-online",  # Use appropriate model
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful research assistant. Provide accurate and detailed information."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "temperature": 0.2,
                "top_p": 0.9,
                "return_citations": True,
                "search_recency_filter": "month",
                **kwargs
            }
            
            # Make API request to correct endpoint
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )
            
            # Handle response
            if response.status_code == 200:
                result = response.json()
                # Extract content from response
                content = result['choices'][0]['message']['content']
                return {
                    'query': query,
                    'response': content,
                    'citations': result.get('citations', []),
                    'usage': result.get('usage', {})
                }
            else:
                self.logger.log(
                    f"API error: {response.status_code} - {response.text}",
                    'error'
                )
                return None
                
        except Exception as e:
            self.logger.log(f"Error executing query: {str(e)}", 'error')
            return None
            
    def validate_api_key(self) -> bool:
        """Validate API key with test query"""
        try:
            test_response = self.execute_query(
                "Test query",
                max_tokens=10
            )
            return bool(test_response)
        except Exception:
            return False
