"""
ParallagonAgent - Base class for autonomous parallel agents

Defines the core behavior and lifecycle of a Parallagon agent. Each agent:
    - Operates independently on its assigned file
    - Maintains its own rhythm of execution  
    - Communicates through file content changes
    - Self-adjusts its activity based on changes detected
"""
from typing import Dict, Any, Optional, List
import re
import time
import openai
import anthropic
import os
from datetime import datetime, timedelta
from pathlib import Path
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
from typing import Dict, Any, Optional, List
import re
import time
import openai
import anthropic
import os
from datetime import datetime, timedelta
from pathlib import Path
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
        self.watch_files = config.get("watch_files", [])
        # Make sure file_path is in watch_files if not already
        if self.file_path not in self.watch_files:
            self.watch_files.append(self.file_path)
        
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


    @agent_error_handler("read_files")
    def read_files(self) -> None:
        """
        Read all relevant files for the agent.
        """
        try:
            # Ensure file exists with proper directory structure
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            if not os.path.exists(self.file_path):
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    initial_content = "# Contenu Initial\n[En attente de contenu à produire...]"
                    f.write(initial_content)
                    self.current_content = initial_content
            else:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.current_content = f.read()
            
            self.other_files = {}
            for file_path in self.watch_files:
                try:
                    # Ensure parent directory exists for watched files too
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    if not os.path.exists(file_path):
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write("# Contenu Initial\n[En attente de contenu...]")
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.other_files[file_path] = f.read()
                except Exception as e:
                    self.logger(f"Warning: Could not read watched file {file_path}: {e}")
                    self.other_files[file_path] = ""

        except Exception as e:
            self.logger(f"❌ Erreur dans read_files: {str(e)}")
            raise

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

    def write_file(self, content: str) -> bool:
        """Write content to file with proper error handling"""
        try:
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # Écrire avec gestion explicite du fichier
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return True
            
        except PermissionError:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur de permission sur {self.file_path}")
            return False
        except IOError as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur d'écriture: {str(e)}")
            return False
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur inattendue: {str(e)}")
            return False

    def determine_actions(self) -> None:
        try:
            self.logger(f"[{self.__class__.__name__}] Analyse du contenu...")
            
            context = {
                "current": self.current_content,
                "other_files": self.other_files
            }
            
            response = self._get_llm_response(context)
            if response and response != self.current_content:
                if self.write_file(response):
                    self.current_content = response
                    self.logger(f"[{self.__class__.__name__}] ✓ Fichier mis à jour")
                else:
                    self.logger(f"[{self.__class__.__name__}] ❌ Échec de la mise à jour")
                    
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur: {str(e)}")

    def _build_prompt(self, context: dict) -> str:
        return f"""Vous êtes l'agent d'évaluation. Votre rôle est de vérifier la qualité du contenu produit.

Contexte actuel :
{self._format_other_files(context)}

IMPORTANT - PHASES DE DÉMARRAGE:
- Au démarrage initial, il est normal qu'il n'y ait pas encore de contenu à évaluer
- Les spécifications et le contenu se construisent progressivement
- Ne pas signaler d'erreur si les fichiers sont vides ou contiennent des placeholders
- Attendre que du contenu réel soit présent avant de commencer l'évaluation

Votre tâche :
1. Vérifier le respect des spécifications (si présentes)
2. Évaluer la qualité du contenu (si présent)
3. Identifier les points à améliorer

Format de réponse :
# Évaluations en Cours
[section: Nom Section]
- Qualité: [✓|⚠️|❌] Commentaire
- Conformité: [✓|⚠️|❌] Commentaire

# Vue d'Ensemble
[progression: X%]
[status: VALIDATED|NEEDS_WORK|REJECTED]

Notes:
- Utiliser ✓ pour valider
- Utiliser ⚠️ pour les améliorations mineures
- Utiliser ❌ pour les problèmes majeurs
- Si pas de contenu à évaluer, indiquer "En attente de contenu à évaluer" """

    def _get_llm_response(self, context: dict) -> str:
        """Get LLM response with fallback between providers"""
        try:
            # Lire le contenu du contexte
            contexte_path = os.path.join(os.path.dirname(self.file_path), "contexte.md")
            selected_files = {}
            if os.path.exists(contexte_path):
                with open(contexte_path, 'r', encoding='utf-8') as f:
                    contexte_content = f.read()
                    # Extraire la section des fichiers pertinents
                    import re
                    files_section = re.search(r'## Fichiers Pertinents Sélectionnés\n(.*?)(?=\n#|$)', 
                                            contexte_content, 
                                            re.DOTALL)
                    if files_section:
                        # Parser les fichiers et leur contenu
                        current_file = None
                        current_content = []
                        for line in files_section.group(1).split('\n'):
                            if line.startswith('### '):
                                if current_file:
                                    selected_files[current_file] = '\n'.join(current_content)
                                current_file = line[4:].strip()
                                current_content = []
                            elif line.strip() and current_file:
                                current_content.append(line)
                        if current_file:
                            selected_files[current_file] = '\n'.join(current_content)

            # Enrichir le contexte avec les fichiers sélectionnés
            enriched_context = {
                **context,
                "contexte_files": selected_files
            }

            # Utiliser le contexte enrichi dans le prompt
            prompt = self._build_prompt(enriched_context)
            
            # Try OpenAI first
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",  # Modèle standard de openai (ne pas remplacer)
                    messages=[{
                        "role": "user", 
                        "content": prompt
                    }],
                    temperature=0,
                    max_tokens=4000
                )
                return response.choices[0].message.content
                
            except Exception as e:
                self.logger(f"[{self.__class__.__name__}] ❌ Erreur OpenAI: {str(e)}")
                
                # Fallback to Anthropic
                try:
                    response = self.client.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=4000,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    return response.content[0].text
                    
                except Exception as e:
                    self.logger(f"[{self.__class__.__name__}] ❌ Erreur Anthropic: {str(e)}")
                    return None
                    
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur dans _get_llm_response: {str(e)}")
            return None

    @agent_error_handler("update")
    def update(self) -> None:
        """Make necessary updates to files based on determined actions."""
        try:
            if hasattr(self, 'new_content') and self.new_content != self.current_content:
                self.logger(f"[{self.__class__.__name__}] Mise à jour du fichier {self.file_path}")
                
                # Utiliser with pour garantir la fermeture du fichier
                try:
                    with open(self.file_path, 'w', encoding='utf-8') as f:
                        f.write(self.new_content)
                    self.current_content = self.new_content
                    self.logger(f"[{self.__class__.__name__}] ✓ Fichier mis à jour")
                    
                    # Notifier du changement si un callback est défini
                    if hasattr(self, 'on_content_changed') and callable(self.on_content_changed):
                        self.on_content_changed(self.file_path, self.new_content)
                        
                except PermissionError:
                    self.logger(f"[{self.__class__.__name__}] ❌ Erreur de permission sur {self.file_path}")
                except IOError as e:
                    self.logger(f"[{self.__class__.__name__}] ❌ Erreur d'écriture: {str(e)}")
                    
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur mise à jour: {str(e)}")
            import traceback
            self.logger(traceback.format_exc())

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
        
        # Format context files first if present
        if "contexte_files" in context:
            formatted.append("\n=== Fichiers Pertinents ===")
            for filename, content in context["contexte_files"].items():
                formatted.append(f"=== {filename} ===\n{content}\n")
        
        # Format other files
        formatted.append("\n=== Autres Fichiers ===")
        for filename, content in context.items():
            if filename != "contexte_files":
                formatted.append(f"=== {filename} ===\n{content}\n")
                
        return "\n".join(formatted)

    def start(self) -> None:
        """Start this individual agent"""
        self.running = True
        # Reset metrics
        self.last_run = None
        self.last_change = None
        self.consecutive_no_changes = 0

    def recover_from_error(self):
        """Try to recover from error state"""
        try:
            self.logger(f"[{self.__class__.__name__}] Attempting recovery...")
            
            # Reset internal state
            self.last_run = None
            self.last_change = None
            self.consecutive_no_changes = 0
            
            # Re-read files
            self.read_files()
            
            # Log recovery attempt
            self.logger(f"[{self.__class__.__name__}] Recovery complete")
            return True
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] Recovery failed: {str(e)}")
            return False

    def update_paths(self, file_path: str, watch_files: List[str]) -> None:
        """Update file paths when mission changes"""
        try:
            self.file_path = file_path
            self.watch_files = watch_files
            
            # Re-read files with new paths
            self.read_files()
            
        except Exception as e:
            print(f"Error updating paths for {self.__class__.__name__}: {e}")

    def stop(self) -> None:
        """
        Stop the agent's execution gracefully.
        
        Ensures:
        - Current operations complete
        - Resources are released
        - State is properly saved
        """
        self.running = False
        # Clean up any pending operations
        if hasattr(self, 'current_content'):
            self.write_file(self.current_content)
            
    def recover_from_error(self):
        """Try to recover from error state"""
        try:
            self.logger(f"[{self.__class__.__name__}] Attempting recovery...")
            
            # Reset internal state
            self.last_run = None
            self.last_change = None
            self.consecutive_no_changes = 0
            
            # Re-read files
            self.read_files()
            
            # Log recovery attempt
            self.logger(f"[{self.__class__.__name__}] Recovery complete")
            return True
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] Recovery failed: {str(e)}")
            return False

    def update_paths(self, file_path: str, watch_files: List[str]) -> None:
        """Update file paths when mission changes"""
        try:
            self.file_path = file_path
            self.watch_files = watch_files
            
            # Re-read files with new paths
            self.read_files()
            
        except Exception as e:
            print(f"Error updating paths for {self.__class__.__name__}: {e}")

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

    def handle_file_change(self, file_name: str, content: str) -> None:
        """
        Handle changes in watched files.
        
        Args:
            file_name: Name of the file that changed
            content: New content of the file
        """
        try:
            # Update other_files with new content
            self.other_files[file_name] = content
            
            # Log the change
            self.logger(f"[{self.__class__.__name__}] File change detected: {file_name}")
            
            # Reset consecutive no changes counter since we detected a change
            self.consecutive_no_changes = 0
            self.last_change = datetime.now()
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] Error handling file change: {str(e)}")

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
        """Main agent lifecycle with improved stop handling"""
        self.running = True
        while self.running:
            try:
                if not self.should_run():
                    time.sleep(1)
                    continue
                    
                # Save state before modifications
                previous_content = self.current_content if hasattr(self, 'current_content') else None
                
                # Execute normal cycle
                self.read_files()
                if not self.running:  # Check if stopped during read
                    break
                    
                self.analyze()
                if not self.running:  # Check if stopped during analysis
                    break
                    
                self.determine_actions()
                if not self.running:  # Check if stopped during action determination
                    break
                    
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
