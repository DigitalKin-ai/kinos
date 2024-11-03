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
from section import Section
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
                self.logger(f"[{self.__class__.__name__}] Modifications détectées, tentative de mise à jour...")
                temp_content = self.current_content

                # Parse and validate TodoList with section-specific tasks
                section_pattern = r'\[section: (.+?)\]\n\[contraintes: (.+?)\](.*?)(?=\[section:|$)'
                task_pattern = r'- \[ \] \[priority: (HIGH|MEDIUM|LOW)\] (.+)$'
                
                todos = ["# TodoList"]
                sections = re.finditer(section_pattern, response, re.MULTILINE | re.DOTALL)
                
                # Dictionary to store tasks by section
                section_todos = {}
                
                for section_match in sections:
                    section_name = section_match.group(1)
                    section_constraints = section_match.group(2)
                    section_content = section_match.group(3)
                    
                    # Initialize task list for this section
                    section_todos[section_name] = []
                    
                    # Extract tasks for this section
                    tasks = re.finditer(task_pattern, section_content, re.MULTILINE)
                    for task_match in tasks:
                        priority = task_match.group(1)
                        task_description = task_match.group(2)
                        section_todos[section_name].append({
                            'priority': priority,
                            'description': task_description
                        })
                    
                    # Add section to TodoList content
                    todos.append(f"\n[section: {section_name}]")
                    todos.append(f"[contraintes: {section_constraints}]")
                    
                    # Add sorted tasks for this section
                    sorted_tasks = self._sort_todos(section_todos[section_name])
                    for task in sorted_tasks:
                        todos.append(f"- [ ] [priority: {task['priority']}] {task['description']}")

                # Update TodoList section
                result = SearchReplace.section_replace(
                    temp_content,
                    "TodoList",
                    '\n'.join(todos[1:])  # Exclude the "# TodoList" title
                )
                
                if result.success:
                    temp_content = result.new_content
                    self.logger(f"[{self.__class__.__name__}] ✓ TodoList mise à jour")

                    # Update Section objects' todo lists
                    self._update_section_todos(section_todos)

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
        return f"""En tant que chef de projet expérimenté, votre rôle est de :
1. Analyser la demande, les spécifications et l'état actuel
2. Définir et prioriser les tâches par section en tenant compte des contraintes
3. Suivre l'avancement et adapter le plan selon les évaluations

Contexte actuel :
{self._format_other_files(context['other_files'])}

Format attendu STRICT à respecter pour chaque section :

# TodoList
[section: Nom Section 1]
[contraintes: contraintes_principales]
- [ ] [priority: HIGH] Tâche prioritaire 1
- [ ] [priority: MEDIUM] Tâche moyenne 1
- [ ] [priority: LOW] Tâche mineure 1

[section: Nom Section 2]
[contraintes: contraintes_principales]
- [ ] [priority: HIGH] Tâche prioritaire 2
- [ ] [priority: MEDIUM] Tâche moyenne 2

Règles STRICTES :
1. Chaque section doit avoir ses propres tâches
2. Les priorités doivent être exactement HIGH, MEDIUM ou LOW
3. Chaque tâche doit commencer par "- [ ] "
4. Les tâches doivent être spécifiques et actionnables
5. Respecter les contraintes de chaque section"""
    def _update_section_todos(self, section_todos: dict) -> None:
        """
        Update todo lists for each section.
        
        Args:
            section_todos: Dictionary mapping section names to their tasks
        """
        try:
            # Read specifications file to get sections
            with open("specifications.md", 'r', encoding='utf-8') as f:
                specs_content = f.read()
                
            # Extract sections and update their todo lists
            section_pattern = r'^# (.+)$'
            for match in re.finditer(section_pattern, specs_content, re.MULTILINE):
                section_name = match.group(1)
                if section_name in section_todos:
                    # Convert tasks to simple list format
                    tasks = [
                        f"[{task['priority']}] {task['description']}"
                        for task in section_todos[section_name]
                    ]
                    
                    # Update section's todo list
                    section = Section(
                        title=section_name,
                        constraints="",  # Will be filled by SpecificationsAgent
                        content=None,    # Will be filled by ProductionAgent
                        evaluation=None, # Will be filled by EvaluationAgent
                        todo=tasks
                    )
                    
                    self.logger(f"[{self.__class__.__name__}] ✓ Updated todos for section: {section_name}")
                    
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Error updating section todos: {str(e)}")
