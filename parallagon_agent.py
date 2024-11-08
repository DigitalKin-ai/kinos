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
    
    # Default intervals for each agent type (in seconds)
    DEFAULT_INTERVALS = {
        'SpecificationsAgent': 20,  # Specifications change less frequently
        'ProductionAgent': 8,       # Medium reactivity
        'ManagementAgent': 15,      # Coordination needs less frequency
        'EvaluationAgent': 18,      # Allow changes to accumulate
        'SuiviAgent': 10            # More reactive monitoring
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
        self.other_files = config.get("other_files", [])
        # Make sure file_path is in other_files if not already
        if self.file_path not in self.other_files:
            self.other_files.append(self.file_path)
        
        # Initialisation des clients API avec les clés validées
        self.client = anthropic.Client(api_key=config["anthropic_api_key"])
        self.openai_client = openai.OpenAI(api_key=config["openai_api_key"])
        
        # Initialize other_files
        self.other_files = {}
        
        # Use agent-specific rhythm or default value
        agent_type = self.__class__.__name__
        self.check_interval = config.get(
            "check_interval", 
            self.DEFAULT_INTERVALS.get(agent_type, 10)
        )
        
        self.running = False
        self.logger = config.get("logger", print)
        self.last_run = None
        self.last_change = None
        self.consecutive_no_changes = 0

    @agent_error_handler("read_files")
    def read_files(self) -> None:
        """
        Read all relevant files for the agent, including all text files in mission folder.
        """
        try:
            # Ensure file exists with proper directory structure
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # Read main file
            if not os.path.exists(self.file_path):
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    initial_content = "# Contenu Initial\n[En attente de contenu à produire...]"
                    f.write(initial_content)
                    self.current_content = initial_content
            else:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.current_content = f.read()
            
            # Reset other_files dictionary
            self.other_files = {}
            
            # Get mission directory from file_path
            mission_dir = os.path.dirname(self.file_path)
            
            # Define text file extensions to include
            TEXT_EXTENSIONS = {'.md', '.txt', '.py', '.js', '.html', '.css', '.json', '.yaml', '.yml'}
            
            # Recursive function to scan directory
            def scan_directory(directory):
                try:
                    for root, _, files in os.walk(directory):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Check if file extension is in our text extensions list
                            if os.path.splitext(file)[1].lower() in TEXT_EXTENSIONS:
                                try:
                                    # Skip the agent's main file as it's already handled
                                    if file_path == self.file_path:
                                        continue
                                        
                                    # Read file content
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        self.other_files[file_path] = f.read()
                                        
                                except Exception as e:
                                    self.logger(f"Warning: Could not read file {file_path}: {e}")
                                    self.other_files[file_path] = ""
                                    
                except Exception as e:
                    self.logger(f"Warning: Error scanning directory {directory}: {e}")

            # Scan mission directory
            scan_directory(mission_dir)
            
            # Also read explicitly watched files that might be outside mission directory
            for file_path in self.other_files:
                if file_path not in self.other_files:  # Skip if already read
                    try:
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
            # Debug log pour voir le chemin exact
            self.logger(f"[{self.__class__.__name__}] Tentative d'écriture dans {self.file_path}")
            
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # Écriture avec gestion explicite du fichier et vérification
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # Vérifier que l'écriture a bien eu lieu
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    written_content = f.read()
                if written_content.strip() == content.strip():
                    self.logger(f"[{self.__class__.__name__}] ✓ Contenu écrit et vérifié")
                    
                    # Notifier du changement via une requête à l'API
                    try:
                        import requests
                        response = requests.post(
                            'http://localhost:8000/api/content/change',
                            json={
                                'file_path': self.file_path,
                                'content': content,
                                'panel_name': self.__class__.__name__.replace('Agent', ''),
                                'flash': True
                            }
                        )
                        if response.status_code == 200:
                            self.logger(f"✓ Notification de changement envoyée")
                        else:
                            self.logger(f"❌ Erreur notification changement: {response.status_code}")
                    except Exception as e:
                        self.logger(f"❌ Erreur envoi notification: {str(e)}")
                    
                    return True
                else:
                    self.logger(f"[{self.__class__.__name__}] ❌ Contenu écrit différent du contenu voulu")
                    return False
                    
            self.logger(f"[{self.__class__.__name__}] ❌ Fichier non trouvé après écriture")
            return False
                
        except PermissionError:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur de permission sur {self.file_path}")
            return False
        except IOError as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur d'écriture: {str(e)}")
            return False
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur inattendue: {str(e)}")
            return False

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

    def start(self) -> None:
        """Start this individual agent"""
        self.running = True
        # Reset metrics
        self.last_run = None
        self.last_change = None
        self.consecutive_no_changes = 0


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

    def update_paths(self, file_path: str, other_files: List[str]) -> None:
        """Update file paths when mission changes"""
        try:
            self.file_path = file_path
            self.other_files = other_files
            
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
