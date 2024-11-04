"""
ProductionAgent - Agent responsible for content creation and implementation.

Key responsibilities:
- Creates and updates content based on specifications
- Implements changes requested by management
- Maintains content quality and consistency 
- Responds to evaluation feedback

Workflow:
1. Monitors specifications and management directives
2. Creates/updates content sections as needed
3. Validates content against requirements
4. Maintains document structure integrity
"""
from parallagon_agent import ParallagonAgent
from search_replace import SearchReplace
import anthropic
import re
from datetime import datetime
from functools import wraps

from functools import wraps

def error_handler(func):
    """Decorator for handling errors in agent methods"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Error: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())
            return args[0].get('production', '') if args else ''
    return wrapper

class ProductionAgent(ParallagonAgent):
    """Agent handling code production and implementation"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = anthropic.Anthropic(api_key=config["anthropic_api_key"])
        self.logger = config.get("logger", print)

    def _needs_update(self, section_name: str) -> bool:
        """Check if a section needs updating"""
        try:
            with open("production.md", 'r', encoding='utf-8') as f:
                content = f.read()
                
            pattern = f"# {section_name}\n(.*?)(?=\n#|$)"
            match = re.search(pattern, content, re.DOTALL)
            
            if not match:
                return True
                
            section_content = match.group(1).strip()
            return section_content == "" or section_content == "[En attente de contenu]"
            
        except Exception:
            return True
            
    def _generate_content(self, section_name: str, constraints: str) -> str:
        """Generate new content for a section"""
        try:
            context = {
                "section_name": section_name,
                "constraints": constraints,
                "other_files": self.other_files
            }
            
            response = self._get_llm_response(context)
            if response and response.strip():
                return response.strip()
                
            return "[En attente de contenu]"
            
        except Exception as e:
            self.logger(f"❌ Error generating content: {str(e)}")
            return "[En attente de contenu]"
            
    def determine_actions(self) -> None:
        """
        Analyze requirements and implement needed content changes.
        
        Process:
        1. Reviews specifications and management directives
        2. Identifies required content updates
        3. Implements changes while maintaining quality
        4. Validates changes against requirements
        5. Updates content sections atomically
        """
        try:
            self.logger(f"[{self.__class__.__name__}] Début de l'analyse...")

            # Extraire les sections existantes avec leur contenu complet
            existing_content = {}
            current_section = None
            current_lines = []
            
            for line in self.current_content.split('\n'):
                if line.startswith('# '):
                    if current_section:
                        existing_content[current_section] = {
                            'content': '\n'.join(current_lines[1:]).strip(),  # Exclure la ligne de titre
                            'full': '\n'.join(current_lines)  # Contenu complet avec titre
                        }
                    current_section = line[2:].strip()
                    current_lines = [line]
                else:
                    current_lines.append(line)
                    
            if current_section:
                existing_content[current_section] = {
                    'content': '\n'.join(current_lines[1:]).strip(),
                    'full': '\n'.join(current_lines)
                }

            # Obtenir les suggestions du LLM
            context = {
                "production": self.current_content,
                "other_files": self.other_files
            }
            
            response = self._get_llm_response(context)
            
            # Extraire les suggestions du LLM
            new_sections = {}
            current_section = None
            current_lines = []
            
            for line in response.split('\n'):
                if line.startswith('# '):
                    if current_section:
                        new_sections[current_section] = '\n'.join(current_lines[1:]).strip()
                    current_section = line[2:].strip()
                    current_lines = [line]
                else:
                    current_lines.append(line)
                    
            if current_section:
                new_sections[current_section] = '\n'.join(current_lines[1:]).strip()

            # Fusionner en ne modifiant que les sections vides
            final_sections = []
            
            for section in existing_content:
                if (existing_content[section]['content'].strip() == '' or 
                    existing_content[section]['content'].strip() == '[En attente de contenu]'):
                    # Section vide ou avec placeholder - utiliser nouvelle suggestion
                    if section in new_sections:
                        final_sections.append(f"# {section}\n{new_sections[section]}")
                    else:
                        final_sections.append(existing_content[section]['full'])
                else:
                    # Section avec contenu existant - préserver
                    final_sections.append(existing_content[section]['full'])

            # Mettre à jour le contenu
            self.new_content = '\n\n'.join(final_sections)
            if self.new_content != self.current_content:
                self.update()
                self.logger(f"[{self.__class__.__name__}] ✓ Contenu mis à jour en préservant l'existant")
            else:
                self.logger(f"[{self.__class__.__name__}] Aucune modification nécessaire")
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur lors de l'analyse: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())

    def _get_llm_response(self, context: dict) -> str:
        """
        Get LLM response for content creation and updates.
        
        Process:
        1. Analyzes current content and requirements
        2. Generates appropriate content updates
        3. Ensures content quality and consistency
        4. Validates response format
        
        Args:
            context: Current content state and requirements
            
        Returns:
            str: Validated content updates
        """
        try:
            self.logger(f"[{self.__class__.__name__}] Calling LLM API...")
            
            prompt = self._build_prompt(context)
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            
            # Modification ici : vérifier si le contenu est substantiel
            if content.strip() and content.strip() != "NO_CHANGES":
                # Vérifier que le contenu contient au moins une section
                if '# ' in content:
                    return content
                else:
                    self.logger(f"[{self.__class__.__name__}] Réponse invalide : pas de sections")
                    return context['production']
                    
            self.logger(f"[{self.__class__.__name__}] No changes needed")
            return context['production']
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] Error calling LLM: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())
            return context['production']

    def _extract_section(self, content: str, section_name: str) -> str:
        """
        Extract content of a specific management section.
        
        Used for:
        - Isolating current directives
        - Accessing task lists
        - Retrieving action history
        
        Args:
            content: Full management content
            section_name: Name of section to extract
            
        Returns:
            str: Content of specified section
        """
        pattern = f"# {section_name}\n(.*?)(?=\n#|$)"
        matches = list(re.finditer(pattern, content, re.DOTALL))
        
        if len(matches) == 0:
            print(f"[{self.__class__.__name__}] Section '{section_name}' not found")
            return ""
        elif len(matches) > 1:
            print(f"[{self.__class__.__name__}] Warning: Multiple '{section_name}' sections found, using first one")
            
        return matches[0].group(1).strip()

    def _format_other_files(self, files: dict) -> str:
        """
        Format other files content for production context.
        
        Organizes:
        - Specifications requirements
        - Management directives
        - Evaluation feedback
        - Related content references
        
        Args:
            files: Dictionary of file contents
            
        Returns:
            str: Formatted context for content decisions
        """
        """
        Format other files content for production context.
        
        Organizes:
        - Specifications requirements
        - Management directives
        - Evaluation feedback
        - Related content references
        
        Args:
            files: Dictionary of file contents
            
        Returns:
            str: Formatted context for content decisions
        """
        result = []
        for file_path, content in files.items():
            result.append(f"=== {file_path} ===\n{content}\n")
        return "\n".join(result)

    def _build_prompt(self, context: dict) -> str:
        """
        Build prompt for content creation and updates.
        
        Includes:
        - Current content state
        - Required changes and updates
        - Quality requirements
        - Format specifications
        - Content guidelines
        
        Args:
            context: Current project state
            
        Returns:
            str: Content creation/update prompt
        """
        """
        Build prompt for content creation and updates.
        
        Includes:
        - Current content state
        - Required changes and updates
        - Quality requirements
        - Format specifications
        - Content guidelines
        
        Args:
            context: Current project state
            
        Returns:
            str: Content creation/update prompt
        """
        return f"""Vous êtes le ProductionAgent, responsable de créer et mettre à jour le contenu des sections.

IMPORTANT - VOS LIMITES :
- Vous ne pouvez PAS créer de nouvelles sections
- Vous ne pouvez PAS supprimer de sections existantes
- Vous ne pouvez PAS modifier la structure du document
- Vous DEVEZ générer du contenu pour les sections vides ou marquées [En attente de contenu]

Contexte actuel :
{self._format_other_files(context['other_files'])}

Instructions STRICTES :
1. Pour chaque section existante :
   - Si elle est vide ou contient [En attente de contenu] : VOUS DEVEZ générer du contenu
   - Si elle a déjà du contenu : ne pas modifier
   - Respecter les contraintes définies dans specifications.md
   - Assurer la cohérence avec les autres sections

2. Le contenu généré doit être :
   - Détaillé et substantiel
   - Pertinent par rapport aux contraintes
   - Bien structuré avec des sous-points si nécessaire
   - En français et professionnel

3. Format de réponse OBLIGATOIRE :
   - Conserver exactement les titres existants
   - Inclure tout le contenu (nouveau et existant)
   - Utiliser la hiérarchie actuelle des sections

NE JAMAIS retourner "NO_CHANGES" si une section est vide ou contient [En attente de contenu].
TOUJOURS générer du contenu pour les sections vides."""
    def _extract_sections(self, content: str) -> dict:
        """
        Extract sections from content while preserving hierarchy.
        
        Used for:
        - Maintaining document structure
        - Processing section-specific updates
        - Preserving content organization
        
        Args:
            content: Full document content
            
        Returns:
            dict: Mapping of section names to content
        """
        """
        Extract sections from content while preserving hierarchy.
        
        Used for:
        - Maintaining document structure
        - Processing section-specific updates
        - Preserving content organization
        
        Args:
            content: Full document content
            
        Returns:
            dict: Mapping of section names to content
        """
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('# '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line.strip()
                current_content = []
            else:
                current_content.append(line)
                
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
            
        return sections
