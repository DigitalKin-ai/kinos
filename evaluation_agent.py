"""
EvaluationAgent - Agent responsible for quality control and validation
"""
from parallagon_agent import ParallagonAgent
from search_replace import SearchReplace
import re
from datetime import datetime
import anthropic

class EvaluationAgent(ParallagonAgent):
    """Agent handling quality control and validation"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = anthropic.Anthropic(api_key=config["anthropic_api_key"])

    def determine_actions(self) -> None:
        """
        Evaluate implementation quality and validate against requirements
        """
        print(f"[{self.__class__.__name__}] Analyzing...")  # Log de debug
        # Prepare context for LLM
        context = {
            "evaluation": self.current_content,
            "other_files": self.other_files
        }
        
        # Get LLM response
        response = self._get_llm_response(context)
        
        if response != self.current_content:
            # Update État Actuel with evaluation status
            result = SearchReplace.section_replace(
                self.current_content,
                "État Actuel",
                self._extract_section(response, "État Actuel")
            )
            if result.success:
                self.current_content = result.new_content

            # Update Contenu Principal with evaluation results
            result = SearchReplace.section_replace(
                self.current_content,
                "Contenu Principal",
                self._extract_section(response, "Contenu Principal")
            )
            if result.success:
                self.current_content = result.new_content

            # Handle evaluation feedback signals
            new_signals = self._extract_section(response, "Signaux")
            if new_signals != self._extract_section(self.current_content, "Signaux"):
                result = SearchReplace.section_replace(
                    self.current_content,
                    "Signaux",
                    new_signals
                )
                if result.success:
                    self.current_content = result.new_content

            # Track evaluation history
            new_history = self._extract_section(response, "Historique")
            if new_history != self._extract_section(self.current_content, "Historique"):
                result = SearchReplace.section_replace(
                    self.current_content,
                    "Historique",
                    new_history
                )
                if result.success:
                    self.current_content = result.new_content

            # Set new content for update
            self.new_content = self.current_content

    def _get_llm_response(self, context: dict) -> str:
        """Get LLM response for evaluation decisions"""
        prompt = f"""You are the Evaluation Agent in the Parallagon framework. Your role is to evaluate quality and validate implementations.

Current evaluation content:
{context['evaluation']}

Other files content:
{self._format_other_files(context['other_files'])}

Your task:
1. Review specifications vs implementation
2. Validate code quality and completeness
3. Check test coverage and results
4. Identify potential improvements
5. Provide detailed feedback

Focus on:
- Requirements compliance
- Code quality metrics
- Test coverage and results
- Performance considerations
- Security aspects
- Documentation completeness

Evaluate and provide feedback on:
- Implementation correctness
- Code structure and organization
- Error handling and edge cases
- Integration points
- Overall quality

If changes are needed, return the complete updated content.
If no changes are needed, return the exact current content.
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
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
            return context['evaluation']

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract content of a specific section"""
        pattern = f"# {section_name}\n(.*?)(?=\n#|$)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _format_other_files(self, files: dict) -> str:
        """Format other files content for the prompt"""
        result = []
        for file_path, content in files.items():
            result.append(f"=== {file_path} ===\n{content}\n")
        return "\n".join(result)
"""
EvaluationAgent - Agent responsible for quality control and validation
"""
import re
from parallagon_agent import ParallagonAgent
import anthropic
from datetime import datetime
from search_replace import SearchReplace

class EvaluationAgent(ParallagonAgent):
    """Agent handling quality control and validation"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = anthropic.Anthropic(api_key=config["anthropic_api_key"])

    def determine_actions(self) -> None:
        """
        Analyze current context and determine if validation/evaluation is needed.
        """
        # Prepare context for LLM
        context = {
            "evaluation": self.current_content,
            "other_files": self.other_files
        }
        
        # Get LLM response
        response = self._get_llm_response(context)
        
        # Apply changes if needed
        if response != self.current_content:
            sections = ["État Actuel", "Signaux", "Contenu Principal", "Historique"]
            
            for section in sections:
                new_section_content = self._extract_section(response, section)
                if new_section_content:
                    result = SearchReplace.section_replace(
                        self.current_content, 
                        section, 
                        new_section_content
                    )
                    if result.success:
                        self.current_content = result.new_content

            # Update status if needed
            self._update_status(response)

            # Set new content for update
            self.new_content = self.current_content

    def _get_llm_response(self, context: dict) -> str:
        """Get LLM response for evaluation tasks"""
        prompt = f"""You are the Evaluation Agent in the Parallagon framework. Your role is to validate work and maintain evaluation.md.

Current evaluation content:
{context['evaluation']}

Other files content:
{self._format_other_files(context['other_files'])}

Your task:
1. Review work from other agents
2. Validate implementation quality
3. Check for validation requests
4. If needed, provide an updated version of evaluation.md that:
   - Evaluates code quality
   - Validates implementations
   - Provides feedback
   - Approves or requests changes
   - Maintains exact markdown structure

Focus on:
- Code quality standards
- Implementation correctness
- Documentation completeness
- Test coverage
- Performance considerations

If no changes are needed, return the exact current content.
If changes are needed, return the complete updated content.

Important:
- Keep all existing sections
- Maintain same formatting
- Only make necessary changes
- Add timestamps for new history entries
- Be precise in evaluation feedback
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
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
            return context['evaluation']

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract content of a specific section"""
        pattern = f"# {section_name}\n(.*?)(?=\n#|$)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _update_status(self, new_content: str) -> None:
        """Update status if changed"""
        old_status_match = re.search(r'\[status: (\w+)\]', self.current_content)
        new_status_match = re.search(r'\[status: (\w+)\]', new_content)
        
        if (old_status_match and new_status_match and 
            old_status_match.group(1) != new_status_match.group(1)):
            result = SearchReplace.exact_replace(
                self.current_content,
                f"[status: {old_status_match.group(1)}]",
                f"[status: {new_status_match.group(1)}]"
            )
            if result.success:
                self.current_content = result.new_content

    def _format_other_files(self, files: dict) -> str:
        """Format other files content for the prompt"""
        result = []
        for file_path, content in files.items():
            result.append(f"=== {file_path} ===\n{content}\n")
        return "\n".join(result)
