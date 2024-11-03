"""
ManagementAgent - Agent responsible for project coordination and planning
"""
from parallagon_agent import ParallagonAgent
from search_replace import SearchReplace
import re
import time
from datetime import datetime
import openai

class ManagementAgent(ParallagonAgent):
    """Agent handling project coordination and task management"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = openai.OpenAI(api_key=config["openai_api_key"])
        self.logger = config.get("logger", print)

    def determine_actions(self) -> None:
        """Analyze project status and coordinate tasks between agents"""
        try:
            self.logger(f"[{self.__class__.__name__}] Début de l'analyse...")
            
            context = {
                "management": self.current_content,
                "other_files": self.other_files
            }
            
            response = self._get_llm_response(context)
            
            if response != self.current_content:
                self.logger(f"[{self.__class__.__name__}] Modifications détectées, tentative de mise à jour...")
                temp_content = self.current_content
                sections = ["Consignes Actuelles", "TodoList", "Actions Réalisées"]
                
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
        """Get LLM response for management decisions"""
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
            time.sleep(10)  # Pause de 10 secondes
            return response.choices[0].message.content
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

    def _build_prompt(self, context: dict) -> str:
        """Build the prompt for the LLM"""
        # Extract sections from specifications
        specs_content = context.get("other_files", {}).get("specifications.md", "")
        template_sections = re.findall(r'^# (.+)$', specs_content, re.MULTILINE)
        sections_list = "\n".join([f"- {section}" for section in template_sections])

        return f"""En tant que chef de projet expérimenté, votre rôle est de :
1. Analyser la demande et les spécifications
2. Définir et prioriser les tâches par section
3. Suivre l'avancement
4. Coordonner le travail

Contexte actuel :
{self._format_other_files(context)}

Sections du template :
{sections_list}

Instructions :
1. Analysez tous les documents pour comprendre l'état actuel
2. Pour chaque section du template, identifiez les tâches nécessaires
3. Priorisez les tâches au sein de chaque section
4. Donnez des consignes claires pour la suite

Format attendu :

# Consignes Actuelles
[Consignes claires et précises pour la prochaine étape, en précisant la section concernée]

# TodoList
[Section 1]
- [ ] Tâche 1.1
- [ ] Tâche 1.2

[Section 2]
- [ ] Tâche 2.1
- [ ] Tâche 2.2

etc...

# Actions Réalisées
- [timestamp] Action effectuée (Section concernée)
etc...

Règles :
- Organisez les tâches par section du template
- Priorisez les tâches au sein de chaque section
- Indiquez toujours la section concernée
- Soyez précis et concis dans les descriptions
- Gardez une trace des actions avec leur section"""
