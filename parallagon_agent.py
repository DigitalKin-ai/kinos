"""
ParallagonAgent - Base class for autonomous parallel agents

Defines the core behavior and lifecycle of a Parallagon agent. Each agent:
- Operates independently on its assigned file
- Maintains its own rhythm of execution
- Communicates through file content changes
- Self-adjusts its activity based on changes detected
"""
import re
import time
import openai
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
from search_replace import SearchReplace, SearchReplaceResult
from functools import wraps

def agent_error_handler(method_name: str):
    """Décorateur générique pour la gestion des erreurs des agents"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                error_msg = f"[{self.__class__.__name__}] ❌ Erreur dans {method_name}: {str(e)}"
                self.logger(error_msg)
                import traceback
                self.logger(traceback.format_exc())
                return None
        return wrapper
    return decorator

def agent_error_handler(method_name: str):
    """Décorateur générique pour la gestion des erreurs des agents"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                error_msg = f"[{self.__class__.__name__}] ❌ Erreur dans {method_name}: {str(e)}"
                self.logger(error_msg)
                import traceback
                self.logger(traceback.format_exc())
                return None
        return wrapper
    return decorator

class ParallagonAgent:
    """
    Foundation for autonomous file-focused agents.
    
    Each agent is responsible for:
    - Monitoring and updating its dedicated file
    - Analyzing changes in related files
    - Making independent decisions
    - Adapting its execution rhythm
    
    Key behaviors:
    - File-based state persistence
    - Self-regulated execution cycles
    - Automatic error recovery
    - Activity-based timing adjustments
    """
    
    # Validation rules for different agent types
    VALIDATION_CONFIGS = {
        'ProductionAgent': {'validate_raw': True},  # Allows raw content updates
        'ManagementAgent': {                        # Requires specific sections
            'required_sections': ["Consignes Actuelles", "TodoList", "Actions Réalisées"]
        },
        'SpecificationsAgent': {                    # Enforces structural rules
            'require_level1_heading': True
        },
        'EvaluationAgent': {                        # Maintains evaluation structure
            'required_sections': ["Évaluations en Cours", "Vue d'Ensemble"]
        }
    }

    # Base execution rhythms for each agent type
    DEFAULT_INTERVALS = {
        'SpecificationsAgent': 30,  # Template changes - slower pace
        'ManagementAgent': 10,      # Coordination updates - medium pace
        'ProductionAgent': 5,       # Content creation - rapid pace
        'EvaluationAgent': 15       # Quality control - moderate pace
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize agent with its operational parameters.
        
        The config defines:
        - File responsibilities (main file and watched files)
        - Communication channels (logging)
        - Execution timing
        """
        # Validation de la configuration
        if not config.get("anthropic_api_key"):
            raise ValueError("anthropic_api_key manquante dans la configuration")
        if not config.get("openai_api_key"):
            raise ValueError("openai_api_key manquante dans la configuration")
            
        self.config = config
        self.file_path = config["file_path"]
        
        # Initialisation des clients API avec les clés validées
        self.client = anthropic.Client(api_key=config["anthropic_api_key"])
        self.openai_client = openai.OpenAI(api_key=config["openai_api_key"])
        
        # Initialize other_files
        self.other_files = {}
        
        # Use agent-specific rhythm or default value
        agent_type = self.__class__.__name__
        self.check_interval = config.get(
            "check_interval", 
            self.DEFAULT_INTERVALS.get(agent_type, 5)
        )
        
        self.running = False
        self.logger = config.get("logger", print)
        self.last_run = None
        self.last_change = None
        self.consecutive_no_changes = 0

    # Validation configurations for different agent types
    VALIDATION_CONFIGS = {
        'ProductionAgent': {'validate_raw': True},
        'ManagementAgent': {'required_sections': ["Consignes Actuelles", "TodoList", "Actions Réalisées"]},
        'SpecificationsAgent': {'require_level1_heading': True},
        'EvaluationAgent': {'required_sections': ["Évaluations en Cours", "Vue d'Ensemble"]}
    }

    def _validate_markdown_response(self, response: str) -> bool:
        """
        Validate that LLM response follows required markdown format.
        
        Validation rules:
        - Checks for required sections based on agent type
        - Validates heading structure
        - Ensures content format compliance
        - Applies agent-specific validation rules
        
        Returns:
            bool: True if response is valid, False otherwise
        """
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


    @agent_error_handler("read_files")
    def read_files(self) -> None:
        """
        Read all relevant files for the agent.
        
        Responsibilities:
        - Reads the agent's primary file into current_content
        - Reads all watched files into other_files dictionary
        - Maintains file state for change detection
        """
        # Ensure file exists
        if not Path(self.file_path).exists():
            with open(self.file_path, 'w', encoding='utf-8') as f:
                initial_content = "# Contenu Initial\n[En attente de contenu à produire...]"
                f.write(initial_content)
                self.current_content = initial_content
        else:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.current_content = f.read()
        
        self.other_files = {}
        for file_path in self.config.get("watch_files", []):
            with open(file_path, 'r', encoding='utf-8') as f:
                self.other_files[file_path] = f.read()

    @agent_error_handler("analyze")
    def analyze(self) -> None:
        """
        Analyze changes and signals in the monitored files.
        """
        try:
            self.logger(f"[{self.__class__.__name__}] Début de l'analyse...")
            
            # Extract current status
            status_match = re.search(r'\[status: (\w+)\]', self.current_content)
            self.current_status = status_match.group(1) if status_match else "UNKNOWN"
            self.logger(f"[{self.__class__.__name__}] Status actuel: {self.current_status}")

            # Extract signals section
            signals_match = re.search(r'# Signaux\n(.*?)(?=\n#|$)', 
                                    self.current_content, 
                                    re.DOTALL)
            if signals_match:
                signals_text = signals_match.group(1).strip()
                self.signals = [s.strip() for s in signals_text.split('\n') if s.strip()]
                if self.signals:
                    self.logger(f"[{self.__class__.__name__}] Signaux détectés: {self.signals}")
            else:
                self.signals = []
                self.logger(f"[{self.__class__.__name__}] Aucun signal détecté")

            # Analyze current content and other files to determine needed actions
            self.determine_actions()

        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur dans analyze: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())

    def determine_actions(self) -> None:
        try:
            self.logger(f"[{self.__class__.__name__}] Début de l'analyse...")
            
            # Lire le contenu actuel de la demande
            demand_content = self.other_files.get("demande.md")
            if not demand_content:
                self.logger(f"[{self.__class__.__name__}] ⚠️ Pas de fichier demande.md trouvé")
                return

            # Comparer avec la dernière demande connue
            if demand_content != getattr(self, '_last_demand', None):
                self.logger(f"[{self.__class__.__name__}] 📝 Nouvelle demande détectée")
                
                # Extraire la structure actuelle
                current_structure = self._parse_template_structure(self.current_content)
                
                # Construire le contexte pour le LLM
                context = {
                    "specifications": self.current_content,
                    "other_files": {"demande.md": demand_content}
                }
                
                # Obtenir la réponse du LLM
                llm_response = self._get_llm_response(context)
                if not llm_response:
                    self.logger(f"[{self.__class__.__name__}] ❌ Pas de réponse du LLM")
                    return
                    
                # Parser la nouvelle structure proposée
                new_structure = self._parse_template_structure(llm_response)
                
                # Log des différences pour debug
                self._log_structure_differences(current_structure, new_structure)
                
                if current_structure != new_structure:
                    self.logger(f"[{self.__class__.__name__}] ✨ Modifications de structure détectées")
                    self.new_content = llm_response
                    self.synchronize_template()
                else:
                    self.logger(f"[{self.__class__.__name__}] ℹ Aucune modification nécessaire")
                    
                # Mettre à jour la dernière demande connue
                self._last_demand = demand_content
                
            else:
                self.logger(f"[{self.__class__.__name__}] ℹ Pas de nouvelle demande")
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur lors de l'analyse: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())

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
        """Get LLM response with fallback between providers"""
        try:
            # Try OpenAI first
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{
                    "role": "user", 
                    "content": self._build_prompt(context)
                }],
                temperature=0,
                max_tokens=4000
            )
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur OpenAI: {str(e)}")
            try:
                # Fallback to Anthropic
                response = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4000,
                    messages=[{
                        "role": "user",
                        "content": self._build_prompt(context)
                    }]
                )
                return response.content
                
            except Exception as e:
                self.logger(f"[{self.__class__.__name__}] ❌ Erreur Anthropic: {str(e)}")
                # Return current content as fallback
                return context.get('specifications', '')

    @agent_error_handler("update")
    def update(self) -> None:
        """
        Make necessary updates to files based on determined actions.
        
        Responsibilities:
        - Validates proposed changes
        - Applies updates to file content
        - Maintains file consistency
        - Logs successful changes
        """
        if hasattr(self, 'new_content') and self.new_content != self.current_content:
            self.logger(f"[{self.__class__.__name__}] Updating file {self.file_path}")
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.new_content)
            self.current_content = self.new_content
            self.logger(f"[{self.__class__.__name__}] ✓ File updated successfully")

    def update_production_file(self, section_name: str, new_content: str) -> bool:
        """
        Update a section in the production.md file.
        
        Args:
            section_name: Name of the section to update
            new_content: New content for the section
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            with open("production.md", 'r', encoding='utf-8') as f:
                content = f.read()
                
            result = SearchReplace.section_replace(content, section_name, new_content)
            if result.success:
                with open("production.md", 'w', encoding='utf-8') as f:
                    f.write(result.new_content)
                self.logger(f"✓ Updated section '{section_name}' in production.md")
                return True
                
            self.logger(f"❌ Failed to update section: {result.message}")
            return False
            
        except Exception as e:
            self.logger(f"❌ Error updating production file: {str(e)}")
            return False

    def update_section(self, section_name: str, new_content: str) -> bool:
        """
        Update a specific section in the markdown file.
        
        Args:
            section_name: Name of the section to update
            new_content: New content for the section
            
        Returns:
            bool: True if update successful, False otherwise
            
        Ensures:
        - Section exists before update
        - Content format is valid
        - Update is atomic
        """
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
        """
        Format the context files for the prompt.
        
        Transforms the raw file contents into a structured format
        suitable for LLM processing, maintaining clear separation
        between different files and their contents.
        
        Returns:
            str: Formatted context string for LLM prompt
        """
        formatted = []
        for filename, content in context.items():
            formatted.append(f"=== {filename} ===\n{content}\n")
        return "\n".join(formatted)

    def stop(self) -> None:
        """
        Stop the agent's execution gracefully.
        
        Ensures:
        - Current operations complete
        - Resources are released
        - State is properly saved
        """
        self.running = False

    def should_run(self) -> bool:
        """
        Determines if agent should execute based on:
        - Time since last execution
        - Recent activity level
        - Dynamic timing adjustments
        """
        now = datetime.now()
        
        # First run
        if self.last_run is None:
            return True
            
        # Calculate dynamic delay
        delay = self.calculate_dynamic_interval()
        
        # Check if enough time has elapsed
        return (now - self.last_run) >= timedelta(seconds=delay)

    def calculate_dynamic_interval(self) -> float:
        """
        Calculate the optimal interval between agent executions.
        
        Factors considered:
        - Recent change frequency
        - System activity level
        - Resource utilization
        - Agent-specific timing requirements
        
        Returns:
            float: Calculated interval in seconds
        """
        base_interval = self.check_interval
        
        # If no recent changes, gradually increase interval
        if self.last_change and self.consecutive_no_changes > 0:
            # Increase interval up to 5x base rhythm
            multiplier = min(5, 1 + (self.consecutive_no_changes * 0.5))
            return base_interval * multiplier
            
        return base_interval

    def run(self) -> None:
        """
        Main agent lifecycle:
        - Reads current state from files
        - Analyzes changes and makes decisions
        - Updates files when needed
        - Self-adjusts timing
        - Handles errors and recovery
        """
        self.running = True
        while self.running:
            try:
                if not self.should_run():
                    time.sleep(1)  # Short pause before next check
                    continue
                    
                # Save state before modifications
                previous_content = self.current_content if hasattr(self, 'current_content') else None
                
                # Execute normal cycle
                self.read_files()
                self.analyze()
                self.determine_actions()
                self.update()
                
                # Update metrics
                self.last_run = datetime.now()
                
                # Check for changes
                if hasattr(self, 'current_content') and previous_content == self.current_content:
                    self.consecutive_no_changes += 1
                else:
                    self.consecutive_no_changes = 0
                    self.last_change = datetime.now()
                
                # Adaptive pause
                time.sleep(1)
                
            except Exception as e:
                self.logger(f"Error in agent loop: {e}")
                if not self.running:
                    break
