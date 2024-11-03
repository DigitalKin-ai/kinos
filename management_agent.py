"""
ManagementAgent - Agent responsible for project coordination and planning
"""
from parallagon_agent import ParallagonAgent
from search_replace import SearchReplace
import re
from datetime import datetime
import anthropic

class ManagementAgent(ParallagonAgent):
    """Agent handling project coordination and task management"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = anthropic.Anthropic(api_key=config["anthropic_api_key"])

    def determine_actions(self) -> None:
        """
        Analyze project status and coordinate tasks between agents
        """
        print(f"[{self.__class__.__name__}] Analyzing...")
        
        # Prepare context for LLM
        context = {
            "management": self.current_content,
            "other_files": self.other_files
        }
        
        # Get LLM response
        response = self._get_llm_response(context)
        
        # Validate response format
        if not response.startswith("# État Actuel"):
            print(f"[{self.__class__.__name__}] Invalid response format, ignoring")
            return
            
        # Log comparison
        print(f"[{self.__class__.__name__}] Comparing responses...")
        if response == self.current_content:
            print(f"[{self.__class__.__name__}] No changes needed")
        else:
            print(f"[{self.__class__.__name__}] Changes detected, updating content")
            
            # Log the differences (first 100 chars)
            print(f"[{self.__class__.__name__}] Current content starts with: {self.current_content[:100]}")
            print(f"[{self.__class__.__name__}] New content starts with: {response[:100]}")
        
        if response != self.current_content:
            # Use temporary content for replacements
            temp_content = self.current_content
            sections = ["État Actuel", "Signaux", "Contenu Principal", "Historique"]
            
            for section in sections:
                pattern = f"# {section}\n(.*?)(?=\n#|$)"
                match = re.search(pattern, response, re.DOTALL)
                if not match:
                    print(f"[{self.__class__.__name__}] {section} section not found in LLM response")
                    continue
                    
                new_section_content = match.group(1).strip()
                result = SearchReplace.section_replace(
                    temp_content,
                    section,
                    new_section_content
                )
                if result.success:
                    temp_content = result.new_content
                    
            self.new_content = temp_content
            print(f"[{self.__class__.__name__}] Changes detected:")
            print(f"Old content: {self.current_content[:100]}...")
            print(f"New content: {self.new_content[:100]}...")

    def _get_llm_response(self, context: dict) -> str:
        """Get LLM response for management decisions"""
        try:
            print(f"[{self.__class__.__name__}] Calling LLM API...")  # Debug log
            prompt = f"""You are the Specifications Agent in the Parallagon framework. Your role is to define and maintain creative writing requirements.

Current specifications content:
{context['specifications']}

Other files content:
{self._format_other_files(context['other_files'])}

Your task:
1. Review the current creative writing specifications
2. Define and clarify writing style, tone, and format requirements
3. Specify literary constraints (rhyme scheme, meter, etc.)
4. Ensure consistency in creative direction
5. Respond to questions about creative requirements

Focus on:
- Literary style guidelines
- Thematic elements
- Structural requirements
- Creative constraints
- Quality criteria

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
Description...

# Signaux
- Signal 1
- Signal 2

# TodoList du Projet
### Phase 1
- [x] Task 1
- [ ] Task 2

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
            return context['management']

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
