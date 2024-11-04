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

    def _sort_todos(self, todos: list[dict]) -> list[dict]:
        """Sort todos by priority"""
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        return sorted(todos, key=lambda x: priority_order[x['priority']])

    def determine_actions(self) -> None:
        try:
            self.logger(f"[{self.__class__.__name__}] Début de l'analyse...")
            
            context = {
                "management": self.current_content,
                "other_files": self.other_files
            }
            
            response = self._get_llm_response(context)
            
            if response != self.current_content:
                self.logger(f"[{self.__class__.__name__}] Modifications détectées, mise à jour...")
                
                # Parse and validate TodoList
                todos = ["# TodoList"]
                task_pattern = r'- \[ \] \[priority: (HIGH|MEDIUM|LOW)\] (.+)$'
                
                # Extract tasks and sort them by priority
                tasks = []
                for match in re.finditer(task_pattern, response, re.MULTILINE):
                    priority = match.group(1)
                    task_description = match.group(2)
                    tasks.append({
                        'priority': priority,
                        'description': task_description
                    })
                
                # Sort tasks
                sorted_tasks = self._sort_todos(tasks)
                
                # Add sorted tasks to content
                for task in sorted_tasks:
                    todos.append(f"- [ ] [priority: {task['priority']}] {task['description']}")
                
                # Update TodoList section
                result = SearchReplace.section_replace(
                    response,
                    "TodoList",
                    '\n'.join(todos[1:])  # Exclude the "# TodoList" title
                )
                
                if result.success:
                    self.new_content = result.new_content
                    self.logger(f"[{self.__class__.__name__}] ✓ Mise à jour complète effectuée")
                else:
                    self.logger(f"[{self.__class__.__name__}] ❌ Échec de la mise à jour: {result.message}")
            else:
                self.logger(f"[{self.__class__.__name__}] Aucune modification nécessaire")
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur lors de l'analyse: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())

    def _get_llm_response(self, context: dict) -> str:
        """Get LLM response with standardized error handling"""
        try:
            self.logger(f"[{self.__class__.__name__}] Calling LLM API...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Modèle standardisé pour tous les agents
                messages=[{
                    "role": "user",
                    "content": self._build_prompt(context)
                }],
                temperature=0,
                max_tokens=4000
            )
            self.logger(f"[{self.__class__.__name__}] LLM response received")
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] Error calling LLM: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())
            return context.get(self.__class__.__name__.lower().replace('agent', ''), '')

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
            self.logger(f"[{self.__class__.__name__}] Section '{section_name}' not found")
            return ""
        elif len(matches) > 1:
            self.logger(f"[{self.__class__.__name__}] Warning: Multiple '{section_name}' sections found, using first one")
            
        return matches[0].group(1).strip()

    def _extract_section_todos(self, section_content: str) -> list[str]:
        """Extract todos from section content"""
        todos = []
        for line in section_content.split('\n'):
            if line.startswith('- [ ]'):
                # Extract priority and task description
                match = re.match(r'- \[ \] \[priority: (HIGH|MEDIUM|LOW)\] (.+)$', line)
                if match:
                    priority = match.group(1)
                    task = match.group(2)
                    todos.append(f"[{priority}] {task}")
        return todos

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
        return f'''En tant que chef de projet experimente, votre role est de :
1. Analyser la demande, les specifications et l'etat actuel
2. Definir et prioriser les taches par section en tenant compte des contraintes
3. Suivre l'avancement et adapter le plan selon les evaluations

Contexte actuel :
{self._format_other_files(context['other_files'])}

Format attendu STRICT a respecter pour chaque section :

# TodoList
[section: Nom Section 1]
[contraintes: contraintes_principales]
- [ ] [priority: HIGH] Tache prioritaire 1
- [ ] [priority: MEDIUM] Tache moyenne 1
- [ ] [priority: LOW] Tache mineure 1

[section: Nom Section 2]
[contraintes: contraintes_principales]
- [ ] [priority: HIGH] Tache prioritaire 2
- [ ] [priority: MEDIUM] Tache moyenne 2

Regles STRICTES :
1. Chaque section doit avoir ses propres taches
2. Les priorites doivent etre exactement HIGH, MEDIUM ou LOW
3. Chaque tache doit commencer par "- [ ] "
4. Les taches doivent etre specifiques et actionnables
5. Respecter les contraintes de chaque section'''
