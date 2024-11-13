"""
ResearchAgent - Agent for automated research using Perplexity API
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from agents.base.agent_base import AgentBase
from utils.logger import Logger
from utils.path_manager import PathManager

class ResearchAgent(AgentBase):
    """
    Agent that performs automated research using Perplexity API.
    
    Workflow:
    1. Extract research questions/topics from content
    2. Generate and execute relevant Perplexity queries
    3. Save and organize research data
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize research agent"""
        super().__init__(config)
        
        # Initialize research-specific attributes
        self.data_dir = os.path.join(self.mission_dir, "research_data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.research_log = os.path.join(self.data_dir, "research_log.jsonl")
        self.query_cache = {}
        
        # Load API configuration
        self.api_config = self._load_api_config()

    def get_prompt(self) -> Optional[str]:
        """Get the current prompt content"""
        try:
            # Use prompt handler to get prompt
            from agents.base.prompt_handler import PromptHandler
            prompt_handler = PromptHandler(self.logger)
            return prompt_handler.get_prompt(self.prompt_file)
        except Exception as e:
            self.logger.log(f"Error getting prompt: {str(e)}", 'error')
            return None

    def _run_aider(self, prompt: str) -> Optional[str]:
        """Execute Aider with the given prompt"""
        try:
            # Build and execute query
            query = self.generate_query(prompt)
            results = self.execute_query(query)
            
            if not results:
                return None
                
            # Format results for Aider
            formatted_results = self._format_research_results([{
                'topic': prompt,
                'query': query,
                'results': results
            }])
            
            return formatted_results
            
        except Exception as e:
            self.logger.log(f"Error running Aider: {str(e)}", 'error')
            return None

    def _load_api_config(self) -> Dict[str, Any]:
        """Load Perplexity API configuration"""
        try:
            config_path = os.path.join(PathManager.get_config_path(), "perplexity_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.log(f"Error loading API config: {str(e)}", 'error')
            return {}

    def extract_research_topics(self, content: str) -> List[str]:
        """Extract research topics using Claude"""
        # Keep existing implementation...

    def generate_query(self, topic: str) -> str:
        """Generate an optimized Perplexity query for a topic"""
        # Keep existing implementation...

    def execute_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Execute query using Perplexity API"""
        # Keep existing implementation...

    def save_research_data(self, topic: str, query: str, results: Dict[str, Any]) -> bool:
        """Save research results to disk"""
        # Keep existing implementation...

    def _specific_mission_execution(self, prompt: str) -> Optional[str]:
        """Execute research mission"""
        # Keep existing implementation...

    def cleanup(self):
        """Cleanup research agent resources"""
        # Keep existing implementation...

    def _format_research_results(self, results: List[Dict[str, Any]]) -> str:
        """Format research results for Aider prompt"""
        # Keep existing implementation...

    def _format_findings(self, results: Dict[str, Any]) -> str:
        """Format query results into readable findings"""
        # Keep existing implementation...
