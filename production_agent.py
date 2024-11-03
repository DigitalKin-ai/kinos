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
        self.logger = config.get("logger", print)

    def determine_actions(self) -> None:
        """Analyze requirements and implement needed code changes"""
        try:
            self.logger(f"[{self.__class__.__name__}] Début de l'analyse...")
            
            context = {
                "production": self.current_content,
                "other_files": self.other_files
            }
            
            response = self._get_llm_response(context)
            
            if response != self.current_content:
                self.logger(f"[{self.__class__.__name__}] Modifications détectées, tentative de mise à jour...")
                self.new_content = response
                self.logger(f"[{self.__class__.__name__}] ✓ Mise à jour complète effectuée")
            else:
                self.logger(f"[{self.__class__.__name__}] Aucune modification nécessaire")
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur lors de l'analyse: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())

    def _get_llm_response(self, context: dict) -> str:
        """Get LLM response for implementation decisions"""
        try:
            self.logger(f"[{self.__class__.__name__}] Calling LLM API...")
            
            prompt = self._build_prompt(context)
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            
            # If LLM indicates no changes needed
            if content.strip() == "NO_CHANGES":
                self.logger(f"[{self.__class__.__name__}] No changes needed")
                return context['production']
                
            # If content is different, return it directly
            if content.strip() != context['production'].strip():
                self.logger(f"[{self.__class__.__name__}] Changes detected")
                return content
                
            # If we get here, no changes needed
            self.logger(f"[{self.__class__.__name__}] No changes needed")
            return context['production']
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] Error calling LLM: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())
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

    def _build_prompt(self, context: dict) -> str:
        """Build prompt for production decisions"""
        return f"""You are the Production Agent in the Parallagon framework, working in parallel with 3 other agents.
Your role is to create and refine content based on specifications and management directives.

Current production content:
{context['production']}

Other files content:
{self._format_other_files(context['other_files'])}

Your task:
1. Review current content against specifications
2. Implement changes requested by management
3. Address evaluation feedback
4. Maintain content quality and consistency

Important:
- Use SEARCH/REPLACE format for changes:
  ```
  SEARCH:
  [exact text to replace]
  
  REPLACE:
  [new text]
  ```
- You can include multiple SEARCH/REPLACE blocks
- Text must match exactly for replacement
- If no changes needed, return "NO_CHANGES"

Guidelines:
- Keep existing content that meets requirements
- Make only necessary changes
- Maintain document structure
- Ensure all sections are complete
- Follow writing style guidelines

Return either "NO_CHANGES" or SEARCH/REPLACE blocks."""
