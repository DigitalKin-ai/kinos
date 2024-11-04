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
            if response and response != self.current_content:
                # Écrire directement dans le fichier
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(response)
                self.current_content = response
                self.logger(f"[{self.__class__.__name__}] ✓ Fichier mis à jour")
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur: {str(e)}")

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
        return f"""Vous êtes l'agent de gestion. Votre rôle est de coordonner le travail et définir les tâches.

Contexte actuel :
{self._format_other_files(context['other_files'])}

Votre tâche :
1. Analyser les spécifications et l'état actuel
2. Définir les tâches prioritaires pour chaque section
3. Suivre l'avancement global

Format de réponse :
# TodoList

[section: Introduction]
- [ ] [priority: HIGH|MEDIUM|LOW] Description tâche
- [ ] [priority: HIGH|MEDIUM|LOW] Description tâche

[section: Section 1]
- [ ] [priority: HIGH|MEDIUM|LOW] Description tâche
- [ ] [priority: HIGH|MEDIUM|LOW] Description tâche

[section: Section N]
- [ ] [priority: HIGH|MEDIUM|LOW] Description tâche

# Vue d'Ensemble
[progression: X%]
[status: EN_COURS|TERMINE|BLOQUE]

IMPORTANT:
- Chaque section doit avoir sa propre liste de tâches
- Les tâches doivent être spécifiques et actionnables
- La priorité doit être explicitement indiquée
- Les tâches complétées doivent être marquées [x]"""
