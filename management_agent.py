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
            # Update TodoList if needed
            result = SearchReplace.section_replace(
                self.current_content,
                "TodoList du Projet",
                self._extract_section(response, "TodoList du Projet")
            )
            if result.success:
                self.current_content = result.new_content

            # Update Priorités Actuelles if needed
            result = SearchReplace.section_replace(
                self.current_content,
                "Priorités Actuelles",
                self._extract_section(response, "Priorités Actuelles")
            )
            if result.success:
                self.current_content = result.new_content

            # Update status if needed
            old_status_match = re.search(r'\[status: (\w+)\]', self.current_content)
            new_status_match = re.search(r'\[status: (\w+)\]', response)
            
            if (old_status_match and new_status_match and 
                old_status_match.group(1) != new_status_match.group(1)):
                result = SearchReplace.exact_replace(
                    self.current_content,
                    f"[status: {old_status_match.group(1)}]",
                    f"[status: {new_status_match.group(1)}]"
                )
                if result.success:
                    self.current_content = result.new_content

            # Add new signals if needed
            new_signals = self._extract_section(response, "Signaux")
            if new_signals != self._extract_section(self.current_content, "Signaux"):
                result = SearchReplace.section_replace(
                    self.current_content,
                    "Signaux",
                    new_signals
                )
                if result.success:
                    self.current_content = result.new_content

            # Set new content for update
            self.new_content = self.current_content

    def _get_llm_response(self, context: dict) -> str:
        """Get LLM response for management decisions"""
        try:
            print(f"[{self.__class__.__name__}] Calling LLM API...")  # Debug log
            prompt = f"""You are the Management Agent in the Parallagon framework. Your role is to coordinate the project and manage tasks.

Current management content:
{context['management']}

Other files content:
{self._format_other_files(context['other_files'])}

Your task:
1. Review all files and current project status
2. Update the TodoList with completed/new tasks
3. Adjust priorities based on progress
4. Add signals to coordinate between agents
5. Update status if needed

Important:
- Return ONLY the markdown content, starting with "# État Actuel"
- Keep all existing sections in exact order:
  1. État Actuel
  2. Signaux
  3. TodoList du Projet
  4. Priorités Actuelles
  5. Blocages Potentiels
  6. Historique
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
