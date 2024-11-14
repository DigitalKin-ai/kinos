"""
ResearchAgent - Agent for automated research using Perplexity API
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from agents.aider.aider_agent import AiderAgent
from utils.perplexity_client import PerplexityClient
from utils.logger import Logger
from utils.path_manager import PathManager

class ResearchAgent(AiderAgent):
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
        
        # Initialize Perplexity client using environment variable
        import os
        perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
        self.perplexity_client = PerplexityClient(api_key=perplexity_api_key)
        
        # Load API configuration
        self.api_config = self._load_api_config()
    def _extract_research_topics(self, content: str) -> List[str]:
        """Extract research topics using Claude"""
        try:
            from anthropic import Anthropic
            client = Anthropic()
            
            prompt = f"""Analyze the following content and identify topics or claims that need research and references:

{content}

List ONLY the specific topics or claims that need references, one per line.
Focus on factual claims, statistics, or technical concepts that should be supported by sources.
Do not include explanations - just the topics/claims themselves.
"""
            
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Split response into individual topics
            topics = [t.strip() for t in response.content[0].text.split('\n') if t.strip()]
            
            self.logger.log(f"Extracted {len(topics)} research topics", 'info')
            return topics
            
        except Exception as e:
            self.logger.log(f"Error extracting topics: {str(e)}", 'error')
            return []

    def _generate_query(self, topic: str) -> str:
        """Generate an optimized Perplexity query for a topic"""
        try:
            from anthropic import Anthropic
            client = Anthropic()
            
            prompt = f"""Convert this research topic into an optimized search query for finding academic/reliable sources:

Topic: {topic}

Generate a single search query that:
1. Uses relevant academic/technical terms
2. Includes key qualifiers for reliable sources
3. Is focused and specific
4. Uses appropriate search operators if needed

Return ONLY the query text, nothing else."""

            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            query = response.content[0].text.strip()
            self.logger.log(f"Generated query: {query}", 'debug')
            return query
            
        except Exception as e:
            self.logger.log(f"Error generating query: {str(e)}", 'error')
            return topic

    def _execute_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Execute query using Perplexity API"""
        try:
            # Check cache first
            if query in self.query_cache:
                self.logger.log(f"Using cached results for: {query}", 'debug')
                return self.query_cache[query]
                
            # Execute query
            results = self.perplexity_client.execute_query(query)
            
            if results:
                # Cache results
                self.query_cache[query] = results
                self._save_research_data(query, results)
                
            return results
            
        except Exception as e:
            self.logger.log(f"Error executing query: {str(e)}", 'error')
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

    def _save_research_data(self, query: str, results: Dict[str, Any]) -> bool:
        """Save research results to disk"""
        try:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'results': results
            }
            
            with open(self.research_log, 'a', encoding='utf-8') as f:
                json.dump(entry, f)
                f.write('\n')
                
            return True
            
        except Exception as e:
            self.logger.log(f"Error saving research data: {str(e)}", 'error')
            return False

    def _format_research_results(self, results: List[Dict[str, Any]]) -> str:
        """Format research results for Aider prompt"""
        formatted = []
        
        for result in results:
            formatted.append(f"Topic: {result['topic']}\n")
            formatted.append(f"Query: {result['query']}\n")
            formatted.append("Findings:\n")
            formatted.append(self._format_findings(result['results']))
            formatted.append("\n---\n")
            
        return "\n".join(formatted)

    def _format_findings(self, results: Dict[str, Any]) -> str:
        """Format query results into readable findings"""
        findings = []
        
        for item in results.get('results', []):
            findings.append(f"- {item['title']}")
            findings.append(f"  Source: {item['url']}")
            findings.append(f"  Summary: {item['summary']}\n")
            
        return "\n".join(findings)

    def _specific_mission_execution(self, prompt: str) -> Optional[str]:
        """Execute research mission"""
        try:
            # Get current content
            content = ""
            for file_path in self.mission_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content += f.read() + "\n\n"
                except Exception as e:
                    self.logger.log(f"Error reading {file_path}: {str(e)}", 'warning')
                    
            # Extract research topics
            topics = self._extract_research_topics(content)
            if not topics:
                self.logger.log("No research topics found", 'info')
                return None
                
            # Process each topic
            research_results = []
            for topic in topics:
                # Generate and execute query
                query = self._generate_query(topic)
                results = self._execute_query(query)
                
                if results:
                    research_results.append({
                        'topic': topic,
                        'query': query,
                        'results': results
                    })
                    
            if not research_results:
                return None
                
            # Format results for Aider
            formatted_results = self._format_research_results(research_results)
            
            # Call Aider to insert references
            aider_prompt = f"""Based on the research results below, update the relevant files to add appropriate references and citations.

Research Results:
{formatted_results}

Instructions:
1. Insert references at appropriate locations in the text
2. Use a consistent citation format
3. Add a References/Bibliography section if needed
4. Preserve existing content and formatting
5. Only add the new references - don't modify other content

Please proceed with the updates now."""

            return super()._run_aider(aider_prompt)
            
        except Exception as e:
            self.logger.log(f"Error in research mission: {str(e)}", 'error')
            return None

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

    def run(self):
        """Main execution loop for research agent"""
        try:
            self.logger.log(f"[{self.name}] 🚀 Starting research agent run loop", 'info')
            
            self.running = True
            while self.running:
                try:
                    # Validate mission directory
                    if not os.path.exists(self.mission_dir):
                        self.logger.log(f"[{self.name}] ❌ Mission directory not found")
                        time.sleep(60)
                        continue

                    # Update file list
                    self.list_files()
                    
                    # Get current prompt
                    prompt = self.get_prompt()
                    if not prompt:
                        self.logger.log(f"[{self.name}] ⚠️ No prompt available")
                        time.sleep(60)
                        continue
                    
                    # Execute research mission
                    result = self._run_aider(prompt)
                    
                    # Update state based on result
                    self.last_run = datetime.now()
                    if result:
                        self.last_change = datetime.now()
                        self.consecutive_no_changes = 0
                    else:
                        self.consecutive_no_changes += 1
                        
                    # Calculate dynamic interval
                    wait_time = self.calculate_dynamic_interval()
                    time.sleep(wait_time)
                    
                except Exception as loop_error:
                    self._handle_error('run_loop', loop_error)
                    time.sleep(5)  # Brief pause before retrying

            self.logger.log(f"[{self.name}] Run loop ended")
            
        except Exception as e:
            # Ignore known benign Aider errors
            if any(err in str(e) for err in [
                "Can't initialize prompt toolkit",
                "No Windows console found",
                "aider.chat/docs/troubleshooting/edit-errors.html",
                "[Errno 22] Invalid argument"
            ]):
                pass  # Do not stop the agent
            else:
                self.logger.log(f"[{self.name}] Critical error in run: {str(e)}", 'error')
                self.running = False
            
        finally:
            # Ensure cleanup happens
            self.cleanup()

    def cleanup(self):
        """Cleanup research agent resources"""
        # Keep existing implementation...

    def _format_research_results(self, results: List[Dict[str, Any]]) -> str:
        """Format research results for Aider prompt"""
        # Keep existing implementation...

    def _format_findings(self, results: Dict[str, Any]) -> str:
        """Format query results into readable findings"""
        # Keep existing implementation...
