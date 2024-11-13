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
        """
        Extract research topics using Claude to analyze content and identify research needs
        
        Args:
            content: Text content to analyze
                
        Returns:
            List of research topics/questions
        """
        try:
            # Prepare context with project files
            files_context = {}
            for file_path in self.mission_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files_context[file_path] = f.read()
                except Exception as e:
                    self.logger.log(f"Error reading file {file_path}: {str(e)}", 'error')

            # Build prompt for Claude
            prompt = f"""Analyze the following content and project context to identify ONE specific research topic or question that needs citations and academic references.

Content to analyze:
{content}

Project context:
{self._format_files_context(files_context)}

Requirements:
1. Select ONE clear research question or statement that needs academic citations
2. The topic should be specific and focused enough for targeted research
3. Choose a topic that would benefit from academic sources and citations
4. Format the response as a single research question or statement

Return ONLY the research question/statement, without any explanation or additional text."""

            # Execute Claude query with timeout
            from utils.managers.timeout_manager import TimeoutManager
            with TimeoutManager.timeout(30):
                result = self._run_aider(prompt)
                
            if not result:
                self.logger.log("No research topics extracted from Claude", 'warning')
                return []

            # Clean and validate the topic
            topic = result.strip()
            if len(topic) < 10:  # Minimum length validation
                self.logger.log("Extracted topic too short", 'warning')
                return []

            self.logger.log(f"Extracted research topic: {topic}", 'info')
            return [topic]

        except Exception as e:
            self.logger.log(f"Error extracting topics: {str(e)}", 'error')
            return []

    def generate_query(self, topic: str) -> str:
        """
        Generate an optimized Perplexity query for a topic
        
        Args:
            topic: Research topic/question
            
        Returns:
            Formatted query string
        """
        try:
            # Remove any existing query prefixes
            topic = topic.lower().replace('research', '').replace('investigate', '').strip()
            
            # Add context-specific prefixes based on topic content
            if '?' in topic:
                # Direct question - use as is
                query = topic
            elif any(w in topic.lower() for w in ['how', 'what', 'why', 'when', 'where']):
                # Question-like statement - add question mark
                query = f"{topic}?"
            else:
                # Statement - convert to research question
                query = f"What are the key findings and current research about {topic}?"
            
            # Add research-focused qualifiers
            qualifiers = [
                "Include recent research",
                "Cite key studies",
                "Focus on verified sources",
                "Provide specific examples"
            ]
            
            # Combine query with qualifiers
            full_query = f"{query} {' '.join(qualifiers)}"
            
            self.logger.log(f"Generated query: {full_query}", 'debug')
            return full_query
            
        except Exception as e:
            self.logger.log(f"Error generating query: {str(e)}", 'error')
            return ""

    def execute_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Execute query using Perplexity API with rate limiting and caching
        
        Args:
            query: Query string to execute
            
        Returns:
            Query results or None on error
        """
        try:
            # Check cache first
            cache_key = hash(query)
            if cache_key in self.query_cache:
                self.logger.log("Using cached query result", 'debug')
                return self.query_cache[cache_key]
            
            # Check rate limits
            if not self._check_rate_limit():
                self.logger.log("Rate limit exceeded, waiting...", 'warning')
                return None
            
            # Initialize Perplexity client
            from utils.perplexity_client import PerplexityClient
            client = PerplexityClient()
            
            # Execute query with default parameters
            result = client.execute_query(
                query=query,
                max_tokens=1000,
                temperature=0.7
            )
            
            if result:
                # Cache successful result
                self.query_cache[cache_key] = result
                self.logger.log("Query executed and cached successfully", 'info')
            else:
                self.logger.log("Query returned no results", 'warning')
            
            return result
            
        except Exception as e:
            self.logger.log(f"Error executing query: {str(e)}", 'error')
            return None

    def save_research_data(self, topic: str, query: str, results: Dict[str, Any]) -> bool:
        """
        Save research results to disk
        
        Args:
            topic: Research topic
            query: Executed query
            results: Query results
            
        Returns:
            bool: Success status
        """
        try:
            # Create entry with metadata
            entry = {
                "timestamp": datetime.now().isoformat(),
                "topic": topic,
                "query": query,
                "results": results
            }
            
            # Append to research log
            with open(self.research_log, 'a', encoding='utf-8') as f:
                json.dump(entry, f)
                f.write('\n')
                
            return True
            
        except Exception as e:
            self.logger.log(f"Error saving research data: {str(e)}", 'error')
            return False

    def _specific_mission_execution(self, prompt: str) -> Optional[str]:
        """Execute research mission"""
        try:
            # Extract research topics
            topics = self.extract_research_topics(prompt)
            if not topics:
                self.logger.log("No research topics found", 'warning')
                return None

            # Format research results for Aider
            research_results = []
            for topic in topics:
                # Generate and execute query
                query = self.generate_query(topic)
                query_results = self.execute_query(query)
                
                if query_results:
                    # Save research data
                    if self.save_research_data(topic, query, query_results):
                        research_results.append({
                            'topic': topic,
                            'query': query,
                            'results': query_results
                        })

            if not research_results:
                return None

            # Build Aider prompt with research results
            aider_prompt = f"""Using the research results below, update the relevant project files to include appropriate citations and academic references.

Research Results:
{self._format_research_results(research_results)}

Original Context:
{prompt}

Instructions:
1. Identify appropriate locations in the project files to add these citations
2. Insert the research findings and references in a clear, academic format
3. Maintain the existing document structure while adding the new information
4. Use a consistent citation style throughout

Please update the files to incorporate this research data while maintaining the existing content structure."""

            # Execute Aider with the research-enhanced prompt
            return self._run_aider(aider_prompt)

        except Exception as e:
            self.logger.log(f"Error in research mission: {str(e)}", 'error')
            return None

    def cleanup(self):
        """Cleanup research agent resources"""
        try:
            super().cleanup()
            self.query_cache.clear()
        except Exception as e:
            self.logger.log(f"Error in cleanup: {str(e)}", 'error')
    def _format_research_results(self, results: List[Dict[str, Any]]) -> str:
        """Format research results for Aider prompt"""
        formatted = []
        for result in results:
            formatted.append(f"""
Topic: {result['topic']}
Query: {result['query']}
Findings:
{self._format_findings(result['results'])}
""")
        return "\n".join(formatted)

    def _format_findings(self, results: Dict[str, Any]) -> str:
        """Format query results into readable findings"""
        # Adapter selon la structure exacte des résultats de Perplexity
        try:
            if 'text' in results:
                return results['text']
            elif 'answer' in results:
                return results['answer']
            elif isinstance(results, str):
                return results
            return json.dumps(results, indent=2)
        except Exception as e:
            self.logger.log(f"Error formatting findings: {str(e)}", 'error')
            return str(results)
