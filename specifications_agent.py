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
            # Lire le template (specifications.md) et le document de sortie
            with open("specifications.md", 'r', encoding='utf-8') as f:
                template = f.read()
            with open("production.md", 'r', encoding='utf-8') as f:
                output = f.read()

            # Extraire les sections du template
            template_sections = re.findall(r'^# (.+)$', template, re.MULTILINE)
            
            # Extraire les sections existantes du document de sortie
            output_sections = re.findall(r'^# (.+)$', output, re.MULTILINE)

            # Sections à ajouter (présentes dans template mais pas dans output)
            sections_to_add = set(template_sections) - set(output_sections)
            
            # Sections à supprimer (présentes dans output mais pas dans template)
            sections_to_remove = set(output_sections) - set(template_sections)

            # Créer le nouveau contenu
            new_content = output
            
            # Supprimer les sections obsolètes
            for section in sections_to_remove:
                pattern = f"# {section}.*?(?=# |$)"
                new_content = re.sub(pattern, '', new_content, flags=re.DOTALL)

            # Ajouter les nouvelles sections
            for section in sections_to_add:
                # Trouver les contraintes dans le template
                constraints = re.search(f"# {section}\n\\[contraintes: (.+?)\\]", 
                                      template, 
                                      re.DOTALL)
                constraints_text = constraints.group(1) if constraints else "À compléter"
                
                new_section = f"\n\n# {section}\n[En attente de contenu - {constraints_text}]\n"
                new_content += new_section

            # Sauvegarder le nouveau contenu
            with open("production.md", 'w', encoding='utf-8') as f:
                f.write(new_content.strip())
                
            self.logger(f"[{self.__class__.__name__}] ✓ Structure du document synchronisée")

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
