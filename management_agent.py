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
        """
        Analyze project status and coordinate tasks between agents.
        
        Process:
        1. Reviews current project state and progress
        2. Identifies blockers and dependencies
        3. Prioritizes tasks across sections
        4. Updates management directives
        5. Coordinates agent activities
        """
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
                sections = ["Consignes Actuelles", "TodoList", "Actions Réalisées"]
                
                for section in sections:
                    pattern = f"# {section}\n(.*?)(?=\n#|$)"
                    match = re.search(pattern, response, re.DOTALL)
                    if not match:
                        self.logger(f"[{self.__class__.__name__}] ❌ Section '{section}' non trouvée dans la réponse LLM")
                        continue
                        
                    new_section_content = match.group(1).strip()
                    result = SearchReplace.section_replace(
                        temp_content,
                        section,
                        new_section_content
                    )
                    
                    if result.success:
                        temp_content = result.new_content
                        self.logger(f"[{self.__class__.__name__}] ✓ Section '{section}' mise à jour avec succès")
                    else:
                        self.logger(f"[{self.__class__.__name__}] ❌ Échec de la mise à jour de la section '{section}': {result.message}")
                
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
4. Coordonner le travail entre les différentes sections

Contexte actuel :
{self._format_other_files(context['other_files'])}

Sections du template et leurs contraintes :
{sections_list}

État de l'évaluation :
{eval_status}

Instructions :
1. Analysez tous les documents pour comprendre l'état actuel et les blocages
2. Pour chaque section du template :
   - Identifiez les tâches nécessaires pour respecter les contraintes
   - Priorisez les tâches selon l'évaluation actuelle
   - Proposez des actions correctives si nécessaire
3. Donnez des consignes claires et actionnables

Format attendu :

# Consignes Actuelles
[Consignes précises pour la prochaine étape]
- Section concernée : [nom de la section]
- Objectif : [but à atteindre]
- Points d'attention : [éléments critiques à surveiller]

# TodoList
[Section 1 - Contraintes principales]
- [ ] Tâche 1.1 (Priorité: Haute/Moyenne/Basse)
- [ ] Tâche 1.2 (Priorité: Haute/Moyenne/Basse)

[Section 2 - Contraintes principales]
- [ ] Tâche 2.1 (Priorité: Haute/Moyenne/Basse)
- [ ] Tâche 2.2 (Priorité: Haute/Moyenne/Basse)

# Actions Réalisées
- [timestamp] Action effectuée (Section: nom_section | Impact: description_impact)

Règles :
- Organisez les tâches par section avec leurs contraintes principales
- Priorisez les tâches selon l'évaluation et les blocages identifiés
- Indiquez toujours la section concernée et l'impact attendu
- Soyez précis et concis dans les descriptions
- Gardez une trace des actions avec leur section et leur impact"""
