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
            # Lire le template et le document de sortie
            with open("specifications.md", 'r', encoding='utf-8') as f:
                template = f.read()
            with open("production.md", 'r', encoding='utf-8') as f:
                output = f.read()

            # Extraire la structure hiérarchique complète du template
            template_structure = {}
            current_section = None
            current_subsection = None
            current_constraints = {}
            
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
            
            for line in output.split('\n'):
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
                    if main_content and not main_content.startswith('[En attente'):
                        new_content.append(main_content)
                    else:
                        new_content.append(f"[En attente de contenu - Contraintes: {section_info['constraints']}]")
                    
                    # Parcourir les sous-sections
                    for subsection_name, subsection_info in section_info['subsections'].items():
                        new_content.append(f"\n## {subsection_name}")
                        
                        if subsection_name in content_parts.get('subsections', {}):
                            subsection_content = content_parts['subsections'][subsection_name]
                            main_subsection_content = subsection_content.get('main', '').strip()
                            if main_subsection_content and not main_subsection_content.startswith('[En attente'):
                                new_content.append(main_subsection_content)
                            else:
                                new_content.append(f"[En attente de contenu - Contraintes: {subsection_info['constraints']}]")
                            
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
                    new_content.append(f"[En attente de contenu - Contraintes: {section_info['constraints']}]")
                    for subsection_name, subsection_info in section_info['subsections'].items():
                        new_content.append(f"\n## {subsection_name}")
                        new_content.append(f"[En attente de contenu - Contraintes: {subsection_info['constraints']}]")
                        for subsubsection in subsection_info['subsubsections']:
                            new_content.append(f"\n### {subsubsection}")
                            new_content.append("[En attente de contenu]")
                
                new_content.append("")  # Ligne vide entre sections

            # Sauvegarder le nouveau contenu
            final_content = '\n'.join(new_content).strip()
            with open("production.md", 'w', encoding='utf-8') as f:
                f.write(final_content)

            # Journaliser les changements
            changes = {
                "added": set(template_structure.keys()) - set(output_structure.keys()),
                "removed": set(output_structure.keys()) - set(template_structure.keys())
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
        """
        Analyze current context and determine template updates.
        
        Process:
        1. Analyzes demand changes and requirements
        2. Updates template structure if needed
        3. Adjusts section constraints based on requirements
        4. Triggers synchronization when template changes
        """
        """
        Analyze current context and determine template updates.
        
        Process:
        1. Analyzes demand changes and requirements
        2. Updates template structure if needed
        3. Adjusts section constraints based on requirements
        4. Triggers synchronization when template changes
        """
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
        Get LLM response for template decisions.
        
        Process:
        1. Sends formatted prompt to LLM
        2. Validates response format and structure
        3. Handles retries on validation failure
        4. Returns validated template updates
        
        Args:
            context: Current state and file contents
            
        Returns:
            str: Validated template updates from LLM
        """
        """
        Get LLM response for template decisions.
        
        Process:
        1. Sends formatted prompt to LLM
        2. Validates response format and structure
        3. Handles retries on validation failure
        4. Returns validated template updates
        
        Args:
            context: Current state and file contents
            
        Returns:
            str: Validated template updates from LLM
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
    def _build_prompt(self, context: dict) -> str:
        """
        Build LLM prompt for template analysis and updates.
        
        Includes:
        - Current template structure
        - Project requirements and constraints
        - Section relationships and hierarchy
        - Validation rules and format requirements
        
        Args:
            context: Current state and file contents
            
        Returns:
            str: Formatted prompt for LLM
        """
        """
        Build LLM prompt for template analysis and updates.
        
        Includes:
        - Current template structure
        - Project requirements and constraints
        - Section relationships and hierarchy
        - Validation rules and format requirements
        
        Args:
            context: Current state and file contents
            
        Returns:
            str: Formatted prompt for LLM
        """
        return f"""En tant que gestionnaire de template, votre rôle est de définir la structure exacte du document final en utilisant 3 niveaux de titres.

Contexte actuel :
{self._format_other_files(context['other_files'])}

Instructions :
1. Analysez la demande pour identifier :
   - Les sections principales (niveau 1 avec #)
   - Les sous-sections logiques (niveau 2 avec ##)
   - Les points détaillés (niveau 3 avec ###)

2. Créez un template complet avec :
   - Sections principales pour les grands thèmes (# Section)
   - Sous-sections pour les composantes majeures (## Sous-section)
   - Sous-sous-sections pour les détails spécifiques (### Détail)
   - Une description des contraintes pour chaque niveau

Format de sortie attendu :

# Section Principale
[contraintes: description des attentes pour cette section]

## Sous-section 1
[contraintes: attentes spécifiques pour cette sous-section]

### Point Détaillé 1.1
### Point Détaillé 1.2

## Sous-section 2
[contraintes: attentes spécifiques pour cette sous-section]

### Point Détaillé 2.1
### Point Détaillé 2.2

Règles :
- Utilisez systématiquement les 3 niveaux de titres (#, ##, ###)
- Chaque section et sous-section doit avoir ses contraintes entre []
- Les sous-sous-sections servent à détailler les points spécifiques
- Maintenez une structure cohérente et hiérarchique
- Soyez précis mais concis dans les descriptions"""
    def _parse_hierarchical_content(self, content: str) -> dict:
        """
        Parse markdown content into hierarchical structure.
        
        Extracts:
        - Main section content
        - Subsection content and constraints
        - Nested hierarchical relationships
        
        Args:
            content: Raw markdown content
            
        Returns:
            dict: Hierarchical representation of content structure
        """
        result = {'main': '', 'subsections': {}}
        current_subsection = None
        current_subsubsection = None
        lines = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                if lines:
                    if current_subsubsection:
                        result['subsections'][current_subsection]['subsubsections'][current_subsubsection] = '\n'.join(lines)
                    elif current_subsection:
                        result['subsections'][current_subsection]['main'] = '\n'.join(lines)
                    else:
                        result['main'] = '\n'.join(lines)
                lines = []
                current_subsection = line[3:].strip()
                current_subsubsection = None
                result['subsections'][current_subsection] = {'main': '', 'subsubsections': {}}
            elif line.startswith('### '):
                if lines:
                    if current_subsubsection:
                        result['subsections'][current_subsection]['subsubsections'][current_subsubsection] = '\n'.join(lines)
                    else:
                        result['subsections'][current_subsection]['main'] = '\n'.join(lines)
                lines = []
                current_subsubsection = line[4:].strip()
            else:
                lines.append(line)
        
        # Traiter le dernier bloc de contenu
        if lines:
            if current_subsubsection:
                result['subsections'][current_subsection]['subsubsections'][current_subsubsection] = '\n'.join(lines)
            elif current_subsection:
                result['subsections'][current_subsection]['main'] = '\n'.join(lines)
            else:
                result['main'] = '\n'.join(lines)
        
        return result
