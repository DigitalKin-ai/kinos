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

    def synchronize_template(self) -> None:
        """Synchronise la structure du document de sortie avec le template"""
        try:
            # Lire le template et le document de sortie
            with open("specifications.md", 'r', encoding='utf-8') as f:
                template = f.read()
            with open("production.md", 'r', encoding='utf-8') as f:
                output = f.read()

            # Extraire les sections et leurs contraintes du template
            template_sections = {}
            matches = re.finditer(r'^# ([^\n]+)\n\[contraintes: ([^\]]+)\]', template, re.MULTILINE)
            for match in matches:
                section_name = match.group(1)
                constraints = match.group(2).strip()
                template_sections[section_name] = constraints

            # Extraire les sections existantes et leur contenu du document de sortie
            output_sections = {}
            current_section = None
            current_content = []
            
            for line in output.split('\n'):
                if line.startswith('# '):
                    if current_section:
                        output_sections[current_section] = '\n'.join(current_content).strip()
                    current_section = line[2:].strip()
                    current_content = []
                elif current_section:
                    current_content.append(line)
                    
            if current_section:
                output_sections[current_section] = '\n'.join(current_content).strip()

            # Construire le nouveau contenu
            new_content = []
            
            # Ajouter les sections dans l'ordre du template
            for section_name, constraints in template_sections.items():
                new_content.append(f"# {section_name}")
                if section_name in output_sections and output_sections[section_name].strip():
                    # Garder le contenu existant
                    new_content.append(output_sections[section_name])
                else:
                    # Ajouter un placeholder pour nouvelle section
                    new_content.append(f"[En attente de contenu - Contraintes: {constraints}]")
                new_content.append("")  # Ligne vide entre sections

            # Sauvegarder le nouveau contenu
            final_content = '\n'.join(new_content).strip()
            with open("production.md", 'w', encoding='utf-8') as f:
                f.write(final_content)

            changes = {
                "added": set(template_sections.keys()) - set(output_sections.keys()),
                "removed": set(output_sections.keys()) - set(template_sections.keys())
            }
            
            if changes["added"] or changes["removed"]:
                added_msg = f"Sections ajoutées: {', '.join(changes['added'])}" if changes["added"] else ""
                removed_msg = f"Sections supprimées: {', '.join(changes['removed'])}" if changes["removed"] else ""
                self.logger(f"[{self.__class__.__name__}] ✓ Structure synchronisée - {added_msg} {removed_msg}")
            else:
                self.logger(f"[{self.__class__.__name__}] ✓ Structure déjà synchronisée")

        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur lors de la synchronisation du template: {str(e)}")

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
                self.logger(f"[{self.__class__.__name__}] Modifications détectées, mise à jour du template...")
                self.new_content = response
                self.update()
                
                # Synchroniser le document de sortie après chaque mise à jour du template
                self.synchronize_template()
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
        return f"""En tant que gestionnaire de template, votre rôle est de définir la structure exacte du document final.

Contexte actuel :
{self._format_other_files(context['other_files'])}

Instructions :
1. Analysez la demande pour identifier toutes les sections nécessaires
2. Créez un template complet avec :
   - Toutes les sections requises (niveau 1 avec #)
   - Une brève description des contraintes pour chaque section
   - L'ordre logique des sections

Format de sortie attendu :

# Section 1
[contraintes: description courte des attentes pour cette section]

# Section 2
[contraintes: description courte des attentes pour cette section]

etc...

Règles :
- Utilisez uniquement des titres de niveau 1 (#)
- Chaque section doit avoir ses contraintes entre []
- Soyez précis mais concis dans les descriptions
- La structure doit être complète et cohérente"""
