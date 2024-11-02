"""
SpecificationsAgent - Agent responsible for requirements analysis and specification
"""
from parallagon_agent import ParallagonAgent
import anthropic
from datetime import datetime

class SpecificationsAgent(ParallagonAgent):
    """Agent handling project specifications and requirements"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = anthropic.Anthropic(api_key=config["anthropic_api_key"])

    def determine_actions(self) -> None:
        """
        Analyze current context and determine if updates are needed.
        The actual decisions will be made by the LLM based on:
        - Current specifications content
        - Other files content
        - Any signals or questions present
        """
        # Prepare context for LLM
        context = {
            "specifications": self.current_content,
            "other_files": self.other_files
        }
        
        # Get LLM response with fixed prompt
        response = self._get_llm_response(context)
        
        # If LLM suggests changes, update the content
        if response != self.current_content:
            self.new_content = response

    def _get_llm_response(self, context: dict) -> str:
        """
        Get LLM response using fixed prompt.
        The LLM will analyze specifications and other files to determine needed updates.
        """
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
- Keep all existing sections
- Maintain the same formatting
- Only make necessary changes
- Add timestamps for new history entries
- Be precise and concise in responses
"""

        try:
            response = self.client.messages.create(
                model="claude-3-sonnet",
                max_tokens=4000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return context['specifications']

    def _format_other_files(self, files: dict) -> str:
        """Format other files content for the prompt"""
        result = []
        for file_path, content in files.items():
            result.append(f"=== {file_path} ===\n{content}\n")
        return "\n".join(result)
