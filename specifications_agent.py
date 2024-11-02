"""
SpecificationsAgent - Agent responsible for requirements analysis and specifications
"""
import re
from parallagon_agent import ParallagonAgent
import anthropic
from datetime import datetime
from search_replace import SearchReplace

class SpecificationsAgent(ParallagonAgent):
    """Agent handling project specifications and requirements"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = anthropic.Anthropic(api_key=config["anthropic_api_key"])

    def determine_actions(self) -> None:
        """
        Analyze current context and determine if updates are needed.
        """
        print(f"[{self.__class__.__name__}] Analyzing...")
        
        # Prepare context for LLM
        context = {
            "specifications": self.current_content,
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
        
        # Apply changes using SearchReplace if needed
        if response != self.current_content:
            # Update each section with detailed logging
            sections = ["État Actuel", "Signaux", "Contenu Principal", "Historique"]
            
            for section in sections:
                # Extract section content from LLM response
                pattern = f"# {section}\n(.*?)(?=\n#|$)"
                match = re.search(pattern, response, re.DOTALL)
                if not match:
                    print(f"[{self.__class__.__name__}] {section} section not found in LLM response")
                    continue
                    
                new_section_content = match.group(1).strip()
                
                # Use SearchReplace to safely update the section
                result = SearchReplace.section_replace(
                    self.current_content, 
                    section, 
                    new_section_content
                )
                
                print(f"[{self.__class__.__name__}] {section} replace: {'✓' if result.success else '❌'} - {result.message}")
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

            # Set new content for update
            self.new_content = self.current_content

    def _get_llm_response(self, context: dict) -> str:
        """
        Get LLM response using fixed prompt.
        The LLM will analyze specifications and other files to determine needed updates.
        """
        try:
            print(f"[{self.__class__.__name__}] Calling LLM API...")  # Debug log
            prompt = f"""You are the Specifications Agent in the Parallagon framework. Your role is to maintain the specifications.md file.

Current specifications content:
{context['specifications']}

Other files content:
{self._format_other_files(context['other_files'])}

Your task:
1. Review the current specifications
2. Check other files for questions or needs related to specifications
3. If needed, provide an updated version of specifications.md that:
   - Answers any questions directed to Specifications
   - Clarifies any unclear points
   - Updates status if needed
   - Adds relevant information to the history section
   - Maintains the exact same markdown structure

If no changes are needed, return the exact current content.
If changes are needed, return the complete updated content.

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

# Contenu Principal
Content...

# Historique
- [Timestamp] Action
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
            return context['specifications']

    def _format_other_files(self, files: dict) -> str:
        """Format other files content for the prompt"""
        result = []
        for file_path, content in files.items():
            result.append(f"=== {file_path} ===\n{content}\n")
        return "\n".join(result)
