"""
SpecificationsAgent - Agent responsible for requirements analysis and specifications
"""
import re
import time
from parallagon_agent import ParallagonAgent
import openai
from datetime import datetime
from search_replace import SearchReplace

class SpecificationsAgent(ParallagonAgent):
    """Agent handling project specifications and requirements"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = openai.OpenAI(api_key=config["openai_api_key"])
        self.logger = config.get("logger", print)

    def determine_actions(self) -> None:
        """Analyze current context and determine if updates are needed."""
        try:
            self.logger(f"[{self.__class__.__name__}] Début de l'analyse...")
            
            context = {
                "specifications": self.current_content,
                "other_files": self.other_files
            }
            
            response = self._get_llm_response(context)
            
            if response != self.current_content:
                self.logger(f"[{self.__class__.__name__}] Modifications détectées, tentative de mise à jour...")
                temp_content = self.current_content
                sections = ["Spécification de Sortie", "Critères de Succès"]
                
                for section in sections:
                    pattern = f"# {section}\n(.*?)(?=\n#|$)"
                    match = re.search(pattern, response, re.DOTALL)
                    if not match:
                        self.logger(f"[{self.__class__.__name__}] ❌ Section '{section}' non trouvée dans la réponse LLM")
                        continue
                        
                    new_section_content = match.group(1).strip()
                    result = SearchReplace.section_replace(
                        temp_content,
                        section,
                        new_section_content
                    )
                    
                    if result.success:
                        temp_content = result.new_content
                        self.logger(f"[{self.__class__.__name__}] ✓ Section '{section}' mise à jour avec succès")
                    else:
                        self.logger(f"[{self.__class__.__name__}] ❌ Échec de la mise à jour de la section '{section}': {result.message}")
                
                self.new_content = temp_content
                self.logger(f"[{self.__class__.__name__}] ✓ Mise à jour complète effectuée")
            else:
                self.logger(f"[{self.__class__.__name__}] Aucune modification nécessaire")
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur lors de l'analyse: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())

    def _get_llm_response(self, context: dict) -> str:
        """
        Get LLM response using fixed prompt.
        The LLM will analyze specifications and other files to determine needed updates.
        """
        try:
            print(f"[{self.__class__.__name__}] Calling LLM API...")  # Debug log
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": self._build_prompt(context)
                }],
                temperature=0,
                max_tokens=4000
            )
            print(f"[{self.__class__.__name__}] LLM response received")  # Debug log
            time.sleep(30)  # Pause de 30 secondes
            return response.choices[0].message.content
        except Exception as e:
            print(f"[{self.__class__.__name__}] Error in LLM response processing: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return context['specifications']

    def _format_other_files(self, files: dict) -> str:
        """Format other files content for the prompt"""
        result = []
        for file_path, content in files.items():
            result.append(f"=== {file_path} ===\n{content}\n")
        return "\n".join(result)
    def _build_prompt(self, context: dict) -> str:
        """Build prompt for specifications decisions"""
        return f"""You are the Specifications Agent in the Parallagon framework, working in parallel with 3 other agents:
- Management Agent: coordinates tasks and tracks progress
- Production Agent: creates and refines content
- Evaluation Agent: validates quality and compliance

Your role is to define the expected output and success criteria that will guide the other agents' work.

Current specifications content:
{context['specifications']}

Other files content:
{self._format_other_files(context['other_files'])}

Your task:
1. Define the expected output format and content
2. Establish detailed success criteria
3. Update based on new requirements

Important:
- Return ONLY the markdown content with exactly these 2 sections:

# Spécification de Sortie
[Detailed description of expected output]

# Critères de Succès
- Main criterion 1
  * Sub-criterion A
  * Sub-criterion B
- Main criterion 2
  * Sub-criterion A
  * Sub-criterion B

Guidelines:
- Be specific and measurable in criteria
- Use hierarchical bullet points
- Focus on output quality
- Include all relevant constraints

If changes are needed, return the complete updated content.
If no changes are needed, return the exact current content."""
