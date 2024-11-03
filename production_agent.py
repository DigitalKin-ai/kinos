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

            # Lire le contenu actuel
            with open(self.file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()

            # Extraire les sections existantes
            existing_sections = {}
            current_section = None
            current_content_lines = []
            
            for line in current_content.split('\n'):
                if line.startswith('# '):
                    if current_section:
                        existing_sections[current_section] = '\n'.join(current_content_lines).strip()
                    current_section = line[2:].strip()
                    current_content_lines = []
                else:
                    current_content_lines.append(line)
                    
            if current_section:
                existing_sections[current_section] = '\n'.join(current_content_lines).strip()

            # Obtenir la réponse du LLM
            context = {
                "production": self.current_content,
                "other_files": self.other_files
            }
            
            response = self._get_llm_response(context)
            
            # Extraire les sections de la réponse
            new_sections = {}
            current_section = None
            current_content_lines = []
            
            for line in response.split('\n'):
                if line.startswith('# '):
                    if current_section:
                        new_sections[current_section] = '\n'.join(current_content_lines).strip()
                    current_section = line[2:].strip()
                    current_content_lines = []
                else:
                    current_content_lines.append(line)
                    
            if current_section:
                new_sections[current_section] = '\n'.join(current_content_lines).strip()

            # Fusionner les sections en préservant le contenu existant
            final_sections = []
            all_sections = set(list(existing_sections.keys()) + list(new_sections.keys()))
            
            for section in all_sections:
                final_sections.append(f"# {section}")
                if section in existing_sections and existing_sections[section].strip():
                    # Garder le contenu existant s'il existe
                    final_sections.append(existing_sections[section])
                elif section in new_sections:
                    # Utiliser le nouveau contenu si la section était vide
                    final_sections.append(new_sections[section])
                else:
                    # Section vide si aucun contenu disponible
                    final_sections.append("[En attente de contenu]")
                
                final_sections.append("")  # Ligne vide entre les sections

            # Mettre à jour le contenu
            self.new_content = '\n'.join(final_sections).strip()
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
                
            return content
                
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

IMPORTANT - SECTION EDITING AND HIERARCHY RULES:
When you want to edit content, you must:
1. Work with the smallest possible sections
2. Use precise markdown heading levels:
   - # For main document sections
   - ## For major subsections
   - ### For detailed subsections
   - #### For specific topics or categories
   - ##### For detailed points
   - ###### For the most granular subdivisions
3. Each section edit should STOP at the next subsection
4. NEVER add comments, notes, or explanations about your changes
5. Return ONLY the section content, without any meta-commentary

Example format:
# Main Section
Overview content...

## Major Topic 2.0
High-level content...

### Detailed Topic 2.1
Specific content...

#### Subtopic 2.1.1
Detailed analysis...

##### Point 2.1.1.1
Specific details...

Guidelines:
- Always use appropriate heading levels for proper content hierarchy
- Don't skip heading levels (e.g., don't go from ## to ####)
- Use deeper heading levels (###, ####, #####) to break down complex topics
- Keep content organized and nested properly
- Each heading level should have meaningful content
- Maintain consistent heading structure throughout the document
- NEVER include comments or notes about your changes
- Return ONLY the content itself

Return either:
1. "NO_CHANGES" if no updates needed
2. The specific section(s) you want to edit, with their exact heading levels and content ONLY"""
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
