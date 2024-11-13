"""
PerplexityClient - Client for interacting with Perplexity API
"""
import os
import json
import requests
from typing import Dict, Any, Optional
from utils.logger import Logger

class PerplexityClient:
    """Client for making Perplexity API requests"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize client with API key"""
        self.api_key = api_key or os.environ.get('PERPLEXITY_API_KEY')
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
            
            # Prepare request data
            data = {
                "query": query,
                **kwargs
            }
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/query",
                headers=headers,
                json=data
            )
            
            # Handle response
            if response.status_code == 200:
                return response.json()
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
