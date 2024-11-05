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
    """
    Agent responsible for managing document template and structure.
    
    Key responsibilities:
    - Maintains the document template and structure
    - Defines section requirements and constraints
    - Ensures structural consistency across documents
    - Synchronizes template changes with production
    - Synchronizes template changes with production
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.client = openai.OpenAI(api_key=config["openai_api_key"])
        self.logger = config.get("logger", print)
        self._last_demand = None

    def should_run(self) -> bool:
        """
        Determines execution timing based on template-specific criteria.
        
        Triggers execution when:
        - New demand is detected
        - Template-Production synchronization needed
        - Regular check interval elapsed
        
        Returns:
            bool: True if agent should execute, False otherwise
        """
        """
        Determines execution timing based on template-specific criteria.
        
        Triggers execution when:
        - New demand is detected
        - Template-Production synchronization needed
        - Regular check interval elapsed
        
        Returns:
            bool: True if agent should execute, False otherwise
        """
        if super().should_run():
            # Check for significant changes
            current_demand = getattr(self, 'other_files', {}).get("demande.md")
            last_demand = getattr(self, '_last_demand', None)
            
            if current_demand != last_demand:
                self._last_demand = current_demand
                return True
                
            # Check if synchronization needed
            if self.needs_synchronization():
                return True
                
            # Otherwise use normal rhythm
            return True
            
        return False

    def needs_synchronization(self) -> bool:
        """
        Check if template-production synchronization is needed.
        
        Verifies:
        - Section structure matches between template and production
        - All required sections are present
        - Section hierarchy is consistent
        
        Returns:
            bool: True if synchronization needed, False otherwise
        """
        """
        Check if template-production synchronization is needed.
        
        Verifies:
        - Section structure matches between template and production
        - All required sections are present
        - Section hierarchy is consistent
        
        Returns:
            bool: True if synchronization needed, False otherwise
        """
        try:
            with open("specifications.md", 'r', encoding='utf-8') as f:
                specs = f.read()
            with open("production.md", 'r', encoding='utf-8') as f:
                prod = f.read()
                
            # Check for structure differences
            specs_sections = set(re.findall(r'^#\s+(.+)$', specs, re.MULTILINE))
            prod_sections = set(re.findall(r'^#\s+(.+)$', prod, re.MULTILINE))
            
            return specs_sections != prod_sections
            
        except Exception:
            return True  # When in doubt, allow execution

    def _create_section(self, section_name: str, constraints: str = "") -> bool:
        """Create a new section in production.md"""
        content = f"# {section_name}\n[contraintes: {constraints}]\n[En attente de contenu]"
        return self.update_production_file(section_name, content)
        
    def _delete_section(self, section_name: str) -> bool:
        """Delete a section from production.md"""
        try:
            with open("production.md", 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = SearchReplace.section_replace(content, section_name, "(to delete)")
            if result.success:
                with open("production.md", 'w', encoding='utf-8') as f:
                    f.write(result.new_content)
                self.logger(f"✓ Deleted section '{section_name}' from production.md")
                return True
                
            self.logger(f"❌ Failed to delete section: {result.message}")
            return False
            
        except Exception as e:
            self.logger(f"❌ Error deleting section: {str(e)}")
            return False
            
    def synchronize_template(self) -> None:
        """
        Synchronize production document structure with template.
        
        Operations:
        - Extracts template structure and constraints
        - Preserves existing content in matching sections
        - Adds missing sections with placeholders
        - Removes obsolete sections
        - Maintains section hierarchy and constraints
        """
        try:
            # Lire le template et le document de production
            with open("specifications.md", 'r', encoding='utf-8') as f:
                template = f.read()
            with open("production.md", 'r', encoding='utf-8') as f:
                production = f.read()

            # Extraire la structure du template
            template_sections = set(re.findall(r'^#\s+(.+)$', template, re.MULTILINE))
            
            # Extraire les sections existantes de production avec leur contenu complet
            existing_content = {}
            current_section = None
            current_lines = []
            
            for line in production.split('\n'):
                if line.startswith('# '):
                    if current_section:
                        existing_content[current_section] = '\n'.join(current_lines)
                    current_section = line[2:].strip()
                    current_lines = [line]
                else:
                    current_lines.append(line)
                    
            if current_section:
                existing_content[current_section] = '\n'.join(current_lines)

            # Construire le nouveau contenu
            new_content = []
            
            # Ajouter les sections du template
            for section in template_sections:
                if section in existing_content:
                    # Garder le contenu existant complet
                    new_content.append(existing_content[section])
                else:
                    # Ajouter nouvelle section avec placeholder
                    new_content.append(f"# {section}\n[En attente de contenu]")
            
            # Initialize data structures
            template_structure = {}
            current_constraints = {}
            current_section = None
            current_subsection = None

            for line in template.split('\n'):
                if line.startswith('# '):  # Section principale
                    if current_section:
                        template_structure[current_section]['constraints'] = current_constraints.get(current_section, '')
                    current_section = line[2:].strip()
                    template_structure[current_section] = {
                        'constraints': '',
                        'subsections': {}
                    }
                    current_subsection = None
                    
                elif line.startswith('[contraintes:'):
                    if current_subsection:
                        template_structure[current_section]['subsections'][current_subsection]['constraints'] = line[12:-1].strip()
                    else:
                        current_constraints[current_section] = line[12:-1].strip()
                        
                elif line.startswith('## '):  # Sous-section
                    current_subsection = line[3:].strip()
                    template_structure[current_section]['subsections'][current_subsection] = {
                        'constraints': '',
                        'subsubsections': []
                    }
                    
                elif line.startswith('### '):  # Sous-sous-section
                    if current_subsection:
                        subsubsection = line[4:].strip()
                        template_structure[current_section]['subsections'][current_subsection]['subsubsections'].append(subsubsection)
            
            # Ajouter les contraintes de la dernière section
            if current_section:
                template_structure[current_section]['constraints'] = current_constraints.get(current_section, '')

            # Extraire la structure actuelle du document de sortie
            output_structure = {}
            current_section = None
            current_content = []
            
            # Use current_content instead of undefined output
            for line in self.current_content.split('\n'):
                if line.startswith('# '):
                    if current_section:
                        output_structure[current_section] = '\n'.join(current_content).strip()
                    current_section = line[2:].strip()
                    current_content = []
                else:
                    current_content.append(line)
                    
            if current_section:
                output_structure[current_section] = '\n'.join(current_content).strip()

            # Construire le nouveau contenu avec la hiérarchie complète
            new_content = []
            
            # Parcourir la structure hiérarchique
            for section_name, section_info in template_structure.items():
                new_content.append(f"# {section_name}")
                
                if section_name in output_structure and output_structure[section_name].strip():
                    existing_content = output_structure[section_name]
                    content_parts = self._parse_hierarchical_content(existing_content)
                    
                    # Ajouter le contenu principal de la section
                    main_content = content_parts.get('main', '').strip()
                    # Ne remplacer que si la section est vide ou contient le message d'attente
                    if not main_content or main_content.startswith('[En attente'):
                        new_content.append(f"[En attente de contenu - Contraintes: {section_info['constraints']}]")
                    else:
                        new_content.append(main_content)  # Préserver le contenu existant
                    
                    # Parcourir les sous-sections
                    for subsection_name, subsection_info in section_info['subsections'].items():
                        new_content.append(f"\n## {subsection_name}")
                        
                        if subsection_name in content_parts.get('subsections', {}):
                            subsection_content = content_parts['subsections'][subsection_name]
                            main_subsection_content = subsection_content.get('main', '').strip()
                            # Ne remplacer que si la sous-section est vide ou contient le message d'attente
                            if not main_subsection_content or main_subsection_content.startswith('[En attente'):
                                new_content.append(f"[En attente de contenu - Contraintes: {subsection_info['constraints']}]")
                            else:
                                new_content.append(main_subsection_content)  # Préserver le contenu existant
                            
                            # Parcourir les sous-sous-sections
                            for subsubsection in subsection_info['subsubsections']:
                                new_content.append(f"\n### {subsubsection}")
                                if subsubsection in subsection_content.get('subsubsections', {}):
                                    subsubsection_content = subsection_content['subsubsections'][subsubsection].strip()
                                    if subsubsection_content and not subsubsection_content.startswith('[En attente'):
                                        new_content.append(subsubsection_content)
                                    else:
                                        new_content.append("[En attente de contenu]")
                                else:
                                    new_content.append("[En attente de contenu]")
                        else:
                            new_content.append(f"[En attente de contenu - Contraintes: {subsection_info['constraints']}]")
                            for subsubsection in subsection_info['subsubsections']:
                                new_content.append(f"\n### {subsubsection}")
                                new_content.append("[En attente de contenu]")
                else:
                    # Nouvelle section avec hiérarchie complète
                    new_content.append(f"[En attente de contenu]\nContraintes: {section_info['constraints']}")
                    for subsection_name, subsection_info in section_info['subsections'].items():
                        new_content.append(f"\n## {subsection_name}")
                        new_content.append(f"[En attente de contenu - Contraintes: {subsection_info['constraints']}]")
                        for subsubsection in subsection_info['subsubsections']:
                            new_content.append(f"\n### {subsubsection}")
                            new_content.append("[En attente de contenu]")
                
                new_content.append("")  # Ligne vide entre sections

            # Sauvegarder le nouveau contenu
            final_content = '\n\n'.join(new_content)
            with open("production.md", 'w', encoding='utf-8') as f:
                f.write(final_content)

            self.logger(f"[{self.__class__.__name__}] ✓ Structure synchronisée en préservant le contenu")

        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur lors de la synchronisation du template: {str(e)}")

    def determine_actions(self) -> None:
        try:
            self.logger(f"[{self.__class__.__name__}] Début de l'analyse...")
            
            # Obtenir la réponse du LLM
            context = {
                "specifications": self.current_content,
                "other_files": self.other_files
            }
            
            response = self._get_llm_response(context)
            if response and response != self.current_content:
                # Log avant la mise à jour
                self.logger(f"[{self.__class__.__name__}] Modifications détectées, mise à jour du fichier...")
                
                # Écrire dans le fichier
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(response)
                self.current_content = response
                
                # Log après la mise à jour
                self.logger(f"[{self.__class__.__name__}] ✓ Fichier mis à jour avec succès")
            else:
                # Log quand aucune modification n'est nécessaire
                self.logger(f"[{self.__class__.__name__}] ≡ Aucune modification nécessaire")
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur: {str(e)}")

    def _get_llm_response(self, context: dict) -> str:
        """Get LLM response with standardized error handling"""
        try:
            self.logger(f"[{self.__class__.__name__}] Calling LLM API...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Modèle standard de openai (ne pas remplacer)
                messages=[{
                    "role": "user",
                    "content": self._build_prompt(context)
                }],
                temperature=0,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            
            # Vérifier que la réponse contient au moins une section
            if not content or '#' not in content:
                self.logger(f"[{self.__class__.__name__}] ⚠️ Réponse LLM invalide")
                return self.current_content  # Retourner le contenu actuel comme fallback
                
            self.logger(f"[{self.__class__.__name__}] ✓ Réponse LLM valide reçue")
            return content
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur LLM: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())
            return self.current_content  # Retourner le contenu actuel en cas d'erreur

    def _log_structure_differences(self, current: dict, new: dict) -> None:
        """Log les différences entre les structures pour debug"""
        self.logger("=== Différences de structure ===")
        
        # Sections principales
        current_sections = set(current.keys())
        new_sections = set(new.keys())
        
        added = new_sections - current_sections
        removed = current_sections - new_sections
        
        if added:
            self.logger(f"Sections ajoutées: {added}")
        if removed:
            self.logger(f"Sections supprimées: {removed}")
            
        # Sous-sections
        for section in current_sections & new_sections:
            current_subsections = set(current[section]['subsections'].keys())
            new_subsections = set(new[section]['subsections'].keys())
            
            added_sub = new_subsections - current_subsections
            removed_sub = current_subsections - new_subsections
            
            if added_sub:
                self.logger(f"Sous-sections ajoutées dans {section}: {added_sub}")
            if removed_sub:
                self.logger(f"Sous-sections supprimées dans {section}: {removed_sub}")

    def _format_other_files(self, files: dict) -> str:
        """
        Format other files content for management context.
        
        Organizes:
        - Agent status reports
        - Task progress updates
        - Coordination signals
        - Project artifacts
        
        Args:
            files: Dictionary of file contents
            
        Returns:
            str: Formatted context for management decisions
        """
        result = []
        for file_path, content in files.items():
            result.append(f"=== {file_path} ===\n{content}\n")
        return "\n".join(result)
    def force_update(self, new_content: str) -> bool:
        """Force update of specifications file"""
        try:
            if new_content != self.current_content:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                self.current_content = new_content
                self.logger(f"[{self.__class__.__name__}] ✓ Mise à jour forcée effectuée")
                return True
            return False
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur lors de la mise à jour forcée: {str(e)}")
            return False

    def _build_prompt(self, context: dict) -> str:
        return f"""Vous êtes l'agent des spécifications. Votre rôle est d'analyser la demande et de définir la structure du document final.

Contexte actuel :
{self._format_other_files(context['other_files'])}

Votre tâche :
1. Analyser la demande dans demande.md
2. Créer les sections nécessaires avec leurs contraintes
3. Définir la structure complète du document

Format de réponse :
# Section 1
[contraintes: exigences pour cette section]

# Section 2
[contraintes: exigences pour cette section]

etc...

Chaque section doit avoir :
- Un titre clair avec #
- Des contraintes entre []
- Une description des exigences"""
    def _parse_hierarchical_content(self, content: str) -> dict:
        """
        Parse le contenu en préservant la hiérarchie complète.
        
        Args:
            content: Contenu à parser
            
        Returns:
            dict: Structure hiérarchique avec:
                - main: contenu principal
                - subsections: dict de sous-sections
                - subsubsections: dict de sous-sous-sections
        """
        result = {
            'main': '',
            'subsections': {},
            'subsubsections': {}
        }
        
        current_section = None
        current_subsection = None
        main_content = []
        current_lines = []
        
        for line in content.split('\n'):
            if line.startswith('## '):  # Sous-section
                if current_section:
                    # Sauvegarder le contenu précédent
                    if current_subsection:
                        result['subsections'][current_subsection]['main'] = '\n'.join(current_lines).strip()
                    else:
                        main_content.extend(current_lines)
                        
                current_subsection = line[3:].strip()
                result['subsections'][current_subsection] = {
                    'main': '',
                    'subsubsections': {}
                }
                current_lines = []
                
            elif line.startswith('### '):  # Sous-sous-section
                if current_subsection:
                    # Sauvegarder le contenu de la sous-section
                    if current_lines:
                        result['subsections'][current_subsection]['main'] = '\n'.join(current_lines).strip()
                    current_lines = []
                    
                    subsubsection = line[4:].strip()
                    result['subsections'][current_subsection]['subsubsections'][subsubsection] = ''
                    current_section = subsubsection
                else:
                    main_content.append(line)
                    
            else:
                current_lines.append(line)
                
        # Sauvegarder le dernier contenu
        if current_subsection and current_lines:
            result['subsections'][current_subsection]['main'] = '\n'.join(current_lines).strip()
        elif current_lines:
            main_content.extend(current_lines)
            
        result['main'] = '\n'.join(main_content).strip()
        
        return result

    def _parse_template_structure(self, content: str) -> dict:
        """Parse le contenu du template en sections distinctes"""
        structure = {}
        current_section = None
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Nouvelle section principale
            if line.startswith('# '):
                current_section = line[2:].strip()
                structure[current_section] = {
                    'constraints': '',
                    'content': '',
                    'subsections': {}
                }
                
                # Collecter le contenu jusqu'au prochain délimiteur
                content_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith(('#')):
                    content_line = lines[i].strip()
                    if content_line.startswith('[contraintes:'):
                        structure[current_section]['constraints'] = content_line[12:-1].strip()
                    elif content_line:
                        content_lines.append(content_line)
                    i += 1
                i -= 1  # Reculer d'une ligne pour le prochain tour
                
                structure[current_section]['content'] = '\n'.join(content_lines)
                
            # Sous-section
            elif line.startswith('## '):
                if current_section:
                    subsection_name = line[3:].strip()
                    structure[current_section]['subsections'][subsection_name] = {
                        'constraints': '',
                        'content': '',
                        'subsubsections': []
                    }
                    
                    # Collecter le contenu jusqu'au prochain délimiteur
                    content_lines = []
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith(('#')):
                        content_line = lines[i].strip()
                        if content_line.startswith('[contraintes:'):
                            structure[current_section]['subsections'][subsection_name]['constraints'] = content_line[12:-1].strip()
                        elif content_line:
                            content_lines.append(content_line)
                        i += 1
                    i -= 1  # Reculer d'une ligne pour le prochain tour
                    
                    structure[current_section]['subsections'][subsection_name]['content'] = '\n'.join(content_lines)
                    
            # Point détaillé
            elif line.startswith('### '):
                if current_section:
                    last_subsection = list(structure[current_section]['subsections'].keys())[-1] if structure[current_section]['subsections'] else None
                    if last_subsection:
                        subsubsection = line[4:].strip()
                        structure[current_section]['subsections'][last_subsection]['subsubsections'].append(subsubsection)
            
            i += 1
        
        return structure
    def _build_hierarchical_content(self, template_structure: dict) -> str:
        """Construit le contenu hiérarchique complet"""
        new_content = []
        
        for section_name, section_info in template_structure.items():
            # Section principale
            new_content.append(f"# {section_name}")
            if section_info['constraints']:
                new_content.append(f"[contraintes: {section_info['constraints']}]")
            new_content.append("[En attente de contenu]")
            
            # Sous-sections
            for subsection_name, subsection_info in section_info['subsections'].items():
                new_content.append(f"\n## {subsection_name}")
                if subsection_info['constraints']:
                    new_content.append(f"[contraintes: {subsection_info['constraints']}]")
                new_content.append("[En attente de contenu]")
                
                # Sous-sous-sections
                for subsubsection in subsection_info['subsubsections']:
                    new_content.append(f"\n### {subsubsection}")
                    new_content.append("[En attente de contenu]")
            
            new_content.append("")  # Ligne vide entre sections
        
        return '\n'.join(new_content)
