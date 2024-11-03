"""
ManagementAgent - Agent responsible for project coordination and planning.

Key responsibilities:
- Coordinates work between agents
- Manages task prioritization and scheduling  
- Tracks project progress and blockers
- Provides direction and guidance to other agents
"""
from parallagon_agent import ParallagonAgent
from search_replace import SearchReplace
import re
import time
from datetime import datetime
import openai

class ManagementAgent(ParallagonAgent):
    """
    Agent responsible for project coordination and planning.
    
    Key responsibilities:
    - Coordinates work between agents
    - Manages task prioritization and scheduling  
    - Tracks project progress and blockers
    - Provides direction and guidance to other agents
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.client = openai.OpenAI(api_key=config["openai_api_key"])
        self.logger = config.get("logger", print)

    def determine_actions(self) -> None:
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

                # Parse and validate Consignes Actuelles
                consignes_pattern = r'# Consignes Actuelles\n\[section: (.+?)\]\n\[objectif: (.+?)\]\n\[attention: (.+?)\]'
                consignes_match = re.search(consignes_pattern, response, re.DOTALL)
                if not consignes_match:
                    self.logger(f"[{self.__class__.__name__}] ❌ Format invalide pour Consignes Actuelles")
                else:
                    result = SearchReplace.section_replace(
                        temp_content,
                        "Consignes Actuelles",
                        response[consignes_match.start(1):consignes_match.end(3)]
                    )
                    if result.success:
                        temp_content = result.new_content
                        self.logger(f"[{self.__class__.__name__}] ✓ Consignes Actuelles mises à jour")

                # Parse and validate TodoList
                section_pattern = r'\[section: (.+?)\]\n\[contraintes: (.+?)\](.*?)(?=\[section:|$)'
                task_pattern = r'- \[ \] \[priority: (HIGH|MEDIUM|LOW)\] (.+)$'
                
                todos = ["# TodoList"]
                sections = re.finditer(section_pattern, response, re.MULTILINE | re.DOTALL)
                
                for section_match in sections:
                    section_name = section_match.group(1)
                    section_constraints = section_match.group(2)
                    section_content = section_match.group(3)
                    
                    todos.append(f"\n[section: {section_name}]")
                    todos.append(f"[contraintes: {section_constraints}]")
                    
                    tasks = re.finditer(task_pattern, section_content, re.MULTILINE)
                    for task_match in tasks:
                        priority = task_match.group(1)
                        task_description = task_match.group(2)
                        todos.append(f"- [ ] [priority: {priority}] {task_description}")

                result = SearchReplace.section_replace(
                    temp_content,
                    "TodoList",
                    '\n'.join(todos[1:])  # Exclude the "# TodoList" title
                )
                
                if result.success:
                    temp_content = result.new_content
                    self.logger(f"[{self.__class__.__name__}] ✓ TodoList mise à jour")

                # Parse and validate Actions Réalisées
                action_pattern = r'\[timestamp: (\d{4}-\d{2}-\d{2} \d{2}:\d{2})\] \[section: (.+?)\] \[impact: (.+?)\] (.+)$'
                actions_section = re.search(r'# Actions Réalisées\n(.*?)(?=\n#|$)', response, re.DOTALL)
                
                if actions_section:
                    actions = re.finditer(action_pattern, actions_section.group(1), re.MULTILINE)
                    valid_actions = []
                    
                    for action in actions:
                        timestamp = action.group(1)
                        section = action.group(2)
                        impact = action.group(3)
                        description = action.group(4)
                        valid_actions.append(
                            f"[timestamp: {timestamp}] [section: {section}] [impact: {impact}] {description}"
                        )
                    
                    if valid_actions:
                        result = SearchReplace.section_replace(
                            temp_content,
                            "Actions Réalisées",
                            '\n'.join(valid_actions)
                        )
                        if result.success:
                            temp_content = result.new_content
                            self.logger(f"[{self.__class__.__name__}] ✓ Actions Réalisées mises à jour")

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
        Get LLM response for management decisions.
        
        Process:
        1. Analyzes project context and agent status
        2. Determines optimal task distribution
        3. Generates coordinated action plans
        4. Validates response format
        
        Args:
            context: Current project state and agent status
            
        Returns:
            str: Validated management directives
        """
        """
        Get LLM response for management decisions.
        
        Process:
        1. Analyzes project context and agent status
        2. Determines optimal task distribution
        3. Generates coordinated action plans
        4. Validates response format
        
        Args:
            context: Current project state and agent status
            
        Returns:
            str: Validated management directives
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
            print(f"[{self.__class__.__name__}] Error calling LLM: {str(e)}")  # Error log
            import traceback
            print(traceback.format_exc())
            return context['management']

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
        Build prompt for management coordination.
        
        Includes:
        - Current project status
        - Agent activities and needs
        - Task priorities and dependencies
        - Coordination requirements
        - Resource allocation guidance
        
        Args:
            context: Current project state
            
        Returns:
            str: Management coordination prompt
        """
        # Extract sections and their constraints from specifications
        specs_content = context.get("other_files", {}).get("specifications.md", "")
        sections_data = []
        
        # Find all sections and their constraints
        section_matches = re.finditer(r'^# (.+)\n\[contraintes: (.+?)\]', specs_content, re.MULTILINE | re.DOTALL)
        for match in section_matches:
            section_name = match.group(1)
            constraints = match.group(2).strip()
            sections_data.append(f"- {section_name}\n  Contraintes: {constraints}")
        
        sections_list = "\n".join(sections_data)

        # Get evaluation status
        eval_content = context.get("other_files", {}).get("evaluation.md", "")
        eval_status = "Pas d'évaluation disponible"
        if eval_content:
            vue_ensemble = re.search(r'# Vue d\'Ensemble\n(.*?)(?=\n#|$)', eval_content, re.DOTALL)
            if vue_ensemble:
                eval_status = vue_ensemble.group(1).strip()

        return f"""En tant que chef de projet expérimenté, votre rôle est de :
1. Analyser la demande, les spécifications et l'état actuel
2. Définir et prioriser les tâches par section en tenant compte des contraintes
3. Suivre l'avancement et adapter le plan selon les évaluations

Contexte actuel :
{self._format_other_files(context['other_files'])}

Sections du template et leurs contraintes :
{sections_list}

Format attendu STRICT à respecter :

# Consignes Actuelles
[section: nom_section]
[objectif: description_objectif]
[attention: points_critiques]

# TodoList
[section: Section 1]
[contraintes: contraintes_principales]
- [ ] [priority: HIGH] Tâche 1.1
- [ ] [priority: MEDIUM] Tâche 1.2
- [ ] [priority: LOW] Tâche 1.3

[section: Section 2]
[contraintes: contraintes_principales]
- [ ] [priority: HIGH] Tâche 2.1
- [ ] [priority: MEDIUM] Tâche 2.2

# Actions Réalisées
[timestamp: YYYY-MM-DD HH:mm] [section: nom_section] [impact: description_impact] Action effectuée

Règles STRICTES de formatage :
1. Chaque section doit commencer par [section: nom]
2. Les priorités doivent être exactement HIGH, MEDIUM ou LOW
3. Le format timestamp doit être YYYY-MM-DD HH:mm
4. Chaque attribut doit être entre crochets avec le format [clé: valeur]
5. Les tâches doivent commencer par "- [ ] " (avec les espaces)"""
