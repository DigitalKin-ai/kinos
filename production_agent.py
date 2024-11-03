"""
ProductionAgent - Agent responsible for code implementation and technical tasks
"""
from parallagon_agent import ParallagonAgent
from search_replace import SearchReplace
import anthropic
import re
from datetime import datetime

class ProductionAgent(ParallagonAgent):
    """Agent handling code production and implementation"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = anthropic.Anthropic(api_key=config["anthropic_api_key"])

    def determine_actions(self) -> None:
        """Analyze requirements and implement needed code changes"""
        print(f"[{self.__class__.__name__}] Analyzing...")
        
        context = {
            "production": self.current_content,
            "other_files": self.other_files
        }
        
        response = self._get_llm_response(context)
        
        if response != self.current_content:
            self.new_content = response

    def _get_llm_response(self, context: dict) -> str:
        """Build prompt for implementation decisions"""
        try:
            print(f"[{self.__class__.__name__}] Calling LLM API...")  # Debug log
            prompt = f"""You are the Production Agent in the Parallagon framework, working in parallel with 3 other agents:
- Specifications Agent: defines output requirements and success criteria
- Management Agent: coordinates tasks and provides directives
- Evaluation Agent: validates quality and compliance

Your role is to create and refine the actual content based on specifications and management directives.

Current production content:
{context['production']}

Other files content:
{self._format_other_files(context['other_files'])}

Your task:
1. Create or update the content according to specifications
2. Follow management directives
3. Ensure all required elements are present
4. Maintain professional quality

Important:
- Return ONLY the actual content
- Do not include version numbers, status indicators, or meta-information
- Do not describe the content - provide the content itself
- Do not include explanatory text or notes
- The response must be the actual deliverable content

If changes are needed, return the complete updated content.
If no changes are needed, return the exact current content."""
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            print(f"[{self.__class__.__name__}] LLM response received")  # Debug log
            return response.content[0].text
        except Exception as e:
            print(f"[{self.__class__.__name__}] Error calling LLM: {str(e)}")  # Error log
            import traceback
            print(traceback.format_exc())
            return context['production']

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract content of a specific section"""
        pattern = f"# {section_name}\n(.*?)(?=\n#|$)"
        matches = list(re.finditer(pattern, content, re.DOTALL))
        
        if len(matches) == 0:
            print(f"[{self.__class__.__name__}] Section '{section_name}' not found")
            return ""
        elif len(matches) > 1:
            print(f"[{self.__class__.__name__}] Warning: Multiple '{section_name}' sections found, using first one")
            
        return matches[0].group(1).strip()

    def _format_other_files(self, files: dict) -> str:
        """Format other files content for the prompt"""
        result = []
        for file_path, content in files.items():
            result.append(f"=== {file_path} ===\n{content}\n")
        return "\n".join(result)
