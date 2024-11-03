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
            print(f"[{self.__class__.__name__}] Calling LLM API...")  # Debug log
            prompt = f"""You are the Production Agent in the Parallagon framework. You must work ONLY using the SEARCH/REPLACE pattern.

Current production content:
{context['production']}

Other files content:
{self._format_other_files(context['other_files'])}

Your task:
1. Analyze the current content and requirements
2. Identify specific sections or elements that need to be updated
3. Return ONLY a list of search/replace operations in this exact format:

SEARCH<<<
[exact text to find]
>>>

REPLACE<<<
[new text to insert]
>>>

Important rules:
- Each SEARCH must match EXACTLY ONE occurrence in the text
- Include enough context in SEARCH to ensure unique matches
- REPLACE must maintain consistent formatting and style
- You can provide multiple SEARCH/REPLACE pairs
- Each pair must be complete and independent
- Do not include any explanations or comments
- If no changes are needed, return "NO_CHANGES"

Example response:
SEARCH<<<
# Technologies Clés
- Point 1
- Point 2
>>>

REPLACE<<<
# Technologies Clés
- Updated point 1
- Updated point 2
- New point 3
>>>

SEARCH<<<
### Impact Économique
Ancien texte...
>>>

REPLACE<<<
### Impact Économique
Nouveau texte...
>>>"""

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            content = response.content[0].text
            if content == "NO_CHANGES":
                return context['production']
                
            # Process SEARCH/REPLACE pairs with improved error handling
            new_content = context['production']
            pairs = re.findall(r'SEARCH<<<\n(.*?)\n>>>\n\nREPLACE<<<\n(.*?)\n>>>', content, re.DOTALL)
            
            if not pairs:
                print(f"[{self.__class__.__name__}] No valid SEARCH/REPLACE pairs found in response")
                return context['production']
                
            for i, (search, replace) in enumerate(pairs, 1):
                search = search.strip()
                replace = replace.strip()
                
                # Validate the search string exists exactly once
                valid, message, count = SearchReplace.validate_replacement(new_content, search)
                if not valid:
                    print(f"[{self.__class__.__name__}] Pair {i}: {message}")
                    continue
                    
                try:
                    result = SearchReplace.exact_replace(new_content, search, replace)
                    if result.success:
                        new_content = result.new_content
                        print(f"[{self.__class__.__name__}] Successfully applied replacement {i}")
                    else:
                        print(f"[{self.__class__.__name__}] Failed to apply replacement {i}: {result.message}")
                except Exception as e:
                    print(f"[{self.__class__.__name__}] Error processing pair {i}: {str(e)}")
                    continue
                    
            return new_content
            
        except Exception as e:
            print(f"[{self.__class__.__name__}] Error calling LLM: {str(e)}")
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
