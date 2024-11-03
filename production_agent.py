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
        """Get LLM response for implementation decisions"""
        try:
            print(f"[{self.__class__.__name__}] Calling LLM API...")  # Debug log
            prompt = f"""You are the Production Agent in the Parallagon framework. Your role is to create and refine the actual text content.

Current production content:
{context['production']}

Other files content:
{self._format_other_files(context['other_files'])}

Your task:
1. Create new text content based on specifications
2. Refine and improve existing content
3. Apply literary techniques and style guidelines
4. Ensure adherence to creative requirements
5. Implement requested revisions

Focus on:
- Writing quality and style
- Creative expression
- Literary devices
- Rhythm and flow
- Thematic consistency

Important:
- Return ONLY the markdown content, starting with "# État Actuel"
- Keep all existing sections in exact order:
  1. État Actuel
  2. Signaux
  3. Contenu Principal
  4. Historique
- Maintain exact markdown formatting
- Do not include any explanatory text
- Do not start with phrases like "Based on my review" or "After analyzing"
- The response must be a valid markdown document that can directly replace the current content

Example format:
# État Actuel
[status: STATUS]
Implementation progress...

# Signaux
- Signal 1
- Signal 2

# Contenu Principal
Technical details...

# Historique
- [Timestamp] Implementation step

If changes are needed, return the complete updated content.
If no changes are needed, return the exact current content.
"""
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
