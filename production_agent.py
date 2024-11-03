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
            
            # Si le LLM indique qu'aucun changement n'est nécessaire
            if content.strip() == "NO_CHANGES":
                self.logger(f"[{self.__class__.__name__}] No changes needed")
                return context['production']
                
            # Traiter chaque section, en commençant par les plus spécifiques (plus de #)
            current_content = context['production']
            
            # Regex qui capture le niveau de titre (nombre de #) et le titre
            section_pattern = r'(#{1,6})\s*([^#\n]+)\n(.*?)(?=\n#{1,6}\s|$)'
            sections = re.finditer(section_pattern, content, re.DOTALL)
            
            # Trier les sections par niveau (plus de # en premier)
            sections = sorted(list(sections), key=lambda m: len(m.group(1)), reverse=True)
            
            for section_match in sections:
                level = len(section_match.group(1))  # Nombre de #
                section_name = section_match.group(2).strip()
                new_section_content = section_match.group(3).strip()
                
                try:
                    # Construire le pattern exact pour ce niveau de titre
                    title_marker = '#' * level
                    result = SearchReplace.section_replace(
                        current_content,
                        f"{title_marker} {section_name}",
                        new_section_content
                    )
                    
                    if result.success:
                        current_content = result.new_content
                        self.logger(f"[{self.__class__.__name__}] Section '{section_name}' (niveau {level}) updated successfully")
                    else:
                        self.logger(f"[{self.__class__.__name__}] Failed to update section '{section_name}' (niveau {level}): {result.message}")
                        
                except Exception as e:
                    self.logger(f"[{self.__class__.__name__}] Error processing section '{section_name}': {str(e)}")
                    continue
                    
            return current_content
                
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

IMPORTANT - SECTION EDITING RULES:
When you want to edit content, you must:
1. Work with the smallest possible sections
2. Use precise markdown heading levels (# to ######)
3. Each section edit should STOP at the next subsection
4. Example format:

## 2.2 Some Section
[Your content for section 2.2 goes here]
[Content continues...]
[Content will automatically stop at ### 2.2.1 or ## 2.3]

### 2.2.1 Subsection
[Don't include this - it's the next section]

Guidelines:
- Edit one small section at a time
- Don't include subsections in your edits
- Each section edit stops at the next heading of any level
- Use the exact heading level (#, ##, ###, etc.) from the original text
- Keep existing content that meets requirements
- Make only necessary changes
- Maintain document structure
- Follow writing style guidelines

Return either:
1. "NO_CHANGES" if no updates needed
2. The specific section(s) you want to edit, with their exact heading levels

Example response:
## 2.2 Technologies Overview
Updated content for just this section...

### 2.3.1 Specific Feature
Updated content for just this subsection..."""
