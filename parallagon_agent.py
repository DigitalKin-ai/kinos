"""
ParallagonAgent - Base class for autonomous parallel agents
"""
import re
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from search_replace import SearchReplace, SearchReplaceResult
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

class ParallagonAgent:
    """Base class for Parallagon autonomous agents"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the agent with configuration"""
        self.config = config
        self.file_path = config["file_path"]
        self.check_interval = config.get("check_interval", 5)
        self.running = False
        self.logger = config.get("logger", print)

    # Validation configurations for different agent types
    VALIDATION_CONFIGS = {
        'ProductionAgent': {'validate_raw': True},
        'ManagementAgent': {'required_sections': ["Consignes Actuelles", "TodoList", "Actions Réalisées"]},
        'SpecificationsAgent': {'require_level1_heading': True},
        'EvaluationAgent': {'required_sections': ["Évaluations en Cours", "Vue d'Ensemble"]}
    }

    def _validate_markdown_response(self, response: str) -> bool:
        """Validate that LLM response follows required markdown format"""
        agent_type = self.__class__.__name__
        config = self.VALIDATION_CONFIGS.get(agent_type, {})
        
        if config.get('validate_raw'):
            return True
            
        if config.get('require_level1_heading'):
            if not re.search(r'^# .+$', response, re.MULTILINE):
                print(f"[{agent_type}] No level 1 headings found")
                return False
                
        required_sections = config.get('required_sections', [])
        for section in required_sections:
            if f"# {section}" not in response:
                print(f"[{agent_type}] Missing required section: {section}")
                return False
                
        return True
            
        # Pour les autres agents (cas par défaut)
        required_sections = ["État Actuel", "Signaux", "Contenu Principal", "Historique"]
        for section in required_sections:
            if f"# {section}" not in response:
                print(f"[{self.__class__.__name__}] Missing required section: {section}")
                return False
            
        return True


    @error_handler
    def read_files(self) -> None:
        """Read all relevant files for the agent"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.current_content = f.read()
        
        self.other_files = {}
        for file_path in self.config.get("watch_files", []):
            with open(file_path, 'r', encoding='utf-8') as f:
                self.other_files[file_path] = f.read()

    @error_handler
    def analyze(self) -> None:
        """Analyze changes and signals"""
        # Extract current status
        status_match = re.search(r'\[status: (\w+)\]', self.current_content)
        self.current_status = status_match.group(1) if status_match else "UNKNOWN"

        # Extract signals section
        signals_match = re.search(r'# Signaux\n(.*?)(?=\n#|$)', 
                                self.current_content, 
                                re.DOTALL)
        if signals_match:
            signals_text = signals_match.group(1).strip()
            self.signals = [s.strip() for s in signals_text.split('\n') if s.strip()]
        else:
            self.signals = []

        # Analyze current content and other files to determine needed actions
        self.determine_actions()

    def determine_actions(self) -> None:
        """Determine what actions need to be taken based on current state"""
        # This method should be implemented by specific agent subclasses
        pass

    def _build_prompt(self, context: dict) -> str:
        """Construction du prompt pour l'évaluateur"""
        # This is a base implementation that should be overridden by subclasses
        return f"""En tant qu'évaluateur qualité extrêmement rigoureux, vous devez analyser méticuleusement chaque section du projet avec un niveau de détail élevé. Votre rôle est d'identifier la moindre incohérence ou imprécision.

Contexte actuel :
{self._format_other_files(context)}

Instructions :
1. Pour chaque section définie dans les spécifications, réalisez une analyse détaillée :
   - Cohérence : vérifiez chaque lien logique avec les autres sections, identifiez toute contradiction
   - Complétude : examinez si tous les points requis sont traités en profondeur
   - Clarté : évaluez la précision du langage, la structure, l'absence d'ambiguïté
   - Respect des critères : confrontez minutieusement chaque élément aux exigences définies

2. Attribuez un statut précis avec justification détaillée :
   [✓] Validé - uniquement si parfaitement conforme
   [⚠️] À améliorer - listez précisément les points à revoir
   [❌] Non conforme - détaillez chaque non-conformité

3. Structurez votre évaluation rigoureuse ainsi :

# Évaluations en Cours
[Pour chaque section du document]
- Cohérence : [statut] analyse détaillée point par point
- Complétude : [statut] liste exhaustive des éléments présents/manquants
- Clarté : [statut] analyse précise de la formulation et structure
- Respect des critères : [statut] confrontation détaillée aux exigences

# Vue d'Ensemble
- Progression : [pourcentage précis avec justification]
- Points forts : [liste détaillée avec exemples concrets]
- Points à améliorer : [liste exhaustive et priorisée]
- Statut global : [EN_COURS/VALIDÉ/À_REVOIR] avec justification

Ne laissez passer aucun détail. Votre évaluation doit être méticuleuse, objective et constructive, en fournissant des exemples précis pour chaque point soulevé."""

    def _get_llm_response(self, context: dict) -> str:
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    temperature=0,
                    messages=[{"role": "user", "content": self._build_prompt(context)}]
                )
                
                content = response.content[0].text
                if self._validate_markdown_response(content):
                    return content
                print(f"[{self.__class__.__name__}] Invalid response format, retrying...")
                
            except Exception as e:
                print(f"[{self.__class__.__name__}] Attempt {attempt+1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    
        return context[self.__class__.__name__.lower().replace('agent', '')]

    @error_handler
    def update(self) -> None:
        """Make necessary updates to files"""
        if hasattr(self, 'new_content') and self.new_content != self.current_content:
            self.logger(f"[{self.__class__.__name__}] Updating file {self.file_path}")
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.new_content)
            self.current_content = self.new_content
            self.logger(f"[{self.__class__.__name__}] ✓ File updated successfully")

    def update_section(self, section_name: str, new_content: str) -> bool:
        """Update a specific section in the markdown file"""
        try:
            result = SearchReplace.section_replace(self.current_content, section_name, new_content)
            if result.success:
                self.new_content = result.new_content
                return True
            print(f"Error updating section: {result.message}")
            return False
        except Exception as e:
            print(f"Error updating section: {e}")
            return False

    def _format_other_files(self, context: dict) -> str:
        """Format the context files for the prompt"""
        formatted = []
        for filename, content in context.items():
            formatted.append(f"=== {filename} ===\n{content}\n")
        return "\n".join(formatted)

    def stop(self) -> None:
        """Stop the agent's execution"""
        self.running = False

    def run(self) -> None:
        """Main agent loop"""
        self.running = True
        while self.running:  # Cette condition doit être vérifiée en premier
            try:
                if not self.running:  # Double vérification
                    break
                self.read_files()
                self.analyze()
                self.determine_actions()
                self.update()
                time.sleep(self.config["check_interval"])
            except Exception as e:
                print(f"Error in agent loop: {e}")
                if not self.running:  # Vérifier aussi ici
                    break
