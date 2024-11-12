"""
AiderAgent - Agent générique utilisant Aider pour les modifications de fichiers.
Chaque instance représente un rôle spécifique (specifications, production, etc.)
mais partage la même logique d'interaction avec Aider.

GESTION DES CHEMINS:
1. Création des fichiers:
   - Utilise des chemins absolus pour garantir la création au bon endroit
   - Structure: missions/<nom_mission>/<fichier>.md
   - Exemple: missions/Mission_1/specifications.md

2. Appel à Aider:
   - Change le dossier courant vers le dossier mission
   - Utilise des chemins relatifs pour tous les fichiers
   - Revient au dossier original après exécution
"""
import traceback
from utils.exceptions import ServiceError
from agents.kinos_agent import KinOSAgent
from utils.path_manager import PathManager
import traceback
from utils.exceptions import ServiceError
from agents.kinos_agent import KinOSAgent
from utils.path_manager import PathManager
from utils.logger import Logger
import os
import subprocess
import time
import asyncio
from datetime import datetime
from typing import Dict, Optional

class AiderAgent(KinOSAgent):
    """Agent using Aider to modify files.
    Each instance represents a specific role (specifications, production, etc.)
    but shares the same interaction logic with Aider."""
    
    
    def _handle_agent_error(self, operation: str, error: Exception) -> None:
        """Centralized error handling for agent operations."""
        self._log(f"[{self.__class__.__name__}] ❌ Error in {operation}: {str(error)}")

    def __init__(self, config: Dict):
        """Initialize agent with minimal configuration"""
        print("\n=== AIDER AGENT INITIALIZATION STARTING ===")
        print(f"Config received: {config}")
        
        try:
            # Initialize logger with thread-safe configuration
            from utils.logger import Logger
            import threading
            self._log_lock = threading.Lock()
            self.logger = Logger()
            
            # Initialize core attributes
            self.name = config.get("name")
            if not self.name:
                raise ValueError("name must be provided in config")
                
            self.mission_dir = config.get("mission_dir")
            if not self.mission_dir:
                raise ValueError("mission_dir must be provided in config")

            # Store original directory
            self.original_dir = os.getcwd()
            
            # Initialize state tracking
            self.running = False
            self.last_run = None
            self.last_change = None
            self.consecutive_no_changes = 0
            self.mission_files = {}
            self._prompt_cache = {}
            
            # Load prompt file path
            self.prompt_file = config.get("prompt_file")
            self.prompt = config.get("prompt", "")

            # Configure UTF-8 encoding
            self._configure_encoding()
            
            with self._log_lock:
                self.logger.log(f"[{self.__class__.__name__}] Initialized as {self.name}")
            
            self._last_request_time = 0
            self._requests_this_minute = 0
            self._rate_limit_window = 60  # 1 minute
            self._max_requests_per_minute = 50  # Adjust based on your rate limit
                              
        except Exception as e:
            print(f"Error during initialization: {str(e)}")
            raise
        
        # Initialize base attributes
        self.name = config["name"]
        self.prompt = config.get("prompt", "")  # Default empty prompt if not specified
        self.prompt_file = config.get("prompt_file")
        self.mission_dir = config.get("mission_dir", "")
        
        # Initialiser les attributs de suivi
        self.running = False
        self.last_run = None
        self.last_change = None
        self.consecutive_no_changes = 0
        
        # Initialiser les caches et listes
        self._prompt_cache = {}
        self.mission_files = {}
        self.watched_files = []
        
        # Initialiser l'intervalle de vérification
        self.check_interval = config.get('check_interval', 60)  # 60 secondes par défaut

        # Logging d'initialisation
        self.logger.log(f"[{self.__class__.__name__}] Initialisé comme {self.name}")

    def _log(self, message: str, level: str = 'info') -> None:
        """Méthode de logging centralisée"""
        self.logger.log(message, level)

    def _get_relative_file_path(self, file_path: str) -> str:
        """Get relative path from mission directory"""
        try:
            mission_dir = PathManager.get_mission_path(self.web_instance.file_manager.current_mission)
            return os.path.relpath(file_path, mission_dir)
        except Exception as e:
            self.logger(f"Error getting relative path: {str(e)}")
            return file_path
        self._prompt_cache = {}
        
        # Initialize watched files list
        self.watched_files = []

        # Ensure timing attributes are initialized
        self.last_run = None
        self.last_change = None
        self.consecutive_no_changes = 0

        self.logger(f"[{self.__class__.__name__}] Initialisé comme {self.name}")

    def _validate_mission_directory(self) -> bool:
        """Vérifie que le dossier de mission est valide et accessible"""
        try:
            if not os.path.exists(self.mission_dir):
                self._log(f"[{self.__class__.__name__}] ❌ Dossier mission non trouvé: {self.mission_dir}")
                return False
                
            if not os.access(self.mission_dir, os.R_OK | os.W_OK):
                self._log(f"[{self.__class__.__name__}] ❌ Permissions insuffisantes sur: {self.mission_dir}")
                return False
                
            self._log(f"[{self.__class__.__name__}] ✓ Dossier mission valide: {self.mission_dir}")
            return True
            
        except Exception as e:
            self._log(f"[{self.__class__.__name__}] ❌ Erreur validation dossier: {str(e)}")
            return False

    def run_aider(self, prompt: str) -> Optional[str]:
        """Version diagnostique de run_aider"""
        try:
            self.logger.log(f"[{self.__class__.__name__}] 🔍 Début de run_aider()", 'debug')
        
            # Validation des préconditions
            if not self._validate_run_conditions(prompt):
                self._log(f"[{self.__class__.__name__}] ❌ Conditions d'exécution non remplies", 'error')
                return None
        
            # Appel du parent avec logging
            result = self._run_aider(prompt)
        
            if result is None:
                self._log(f"[{self.__class__.__name__}] ⚠️ Aucun résultat de run_aider", 'warning')
            else:
                self._log(f"[{self.__class__.__name__}] ✅ run_aider exécuté avec succès", 'success')
        
            return result
    
        except Exception as e:
            self.logger.log(
                f"[{self.__class__.__name__}] 🔥 Erreur dans run_aider:\n"
                f"{traceback.format_exc()}", 
                'critical'
            )
            return None

    def _handle_rate_limit_error(self, attempt: int, max_attempts: int = 5) -> bool:
        """
        Handle rate limit errors with aggressive exponential backoff
        
        Args:
            attempt: Current attempt number
            max_attempts: Maximum number of retry attempts
            
        Returns:
            bool: True if should retry, False if max attempts exceeded
        """
        if attempt >= max_attempts:
            self._log(
                f"[{self.__class__.__name__}] ❌ Max retry attempts ({max_attempts}) exceeded for rate limit",
                'error'
            )
            return False
            
        # More aggressive backoff: 5s, 15s, 45s, 135s, 405s
        wait_time = 5 * (3 ** (attempt - 1))
        
        self._log(
            f"[{self.__class__.__name__}] ⏳ Rate limit hit (attempt {attempt}/{max_attempts}). "
            f"Waiting {wait_time} seconds before retry...",
            'warning'
        )
        
        time.sleep(wait_time)
        return True

    def _check_rate_limit(self) -> bool:
        """
        Check if we should wait before making another request
        Returns: True if ok to proceed, False if should wait
        """
        current_time = time.time()
        
        # Reset counter if we're in a new minute
        if current_time - self._last_request_time > self._rate_limit_window:
            self._requests_this_minute = 0
            
        # Check if we're approaching the limit
        if self._requests_this_minute >= self._max_requests_per_minute:
            wait_time = self._rate_limit_window - (current_time - self._last_request_time)
            if wait_time > 0:
                self._log(
                    f"[{self.__class__.__name__}] ⏳ Approaching rate limit. "
                    f"Waiting {wait_time:.1f}s before next request.",
                    'warning'
                )
                time.sleep(wait_time)
                self._requests_this_minute = 0
                
        self._last_request_time = current_time
        self._requests_this_minute += 1
        return True

    def _run_aider(self, prompt: str) -> Optional[str]:
        """Execute Aider with given prompt and stream output."""
        try:
            # Check rate limit before proceeding
            if not self._check_rate_limit():
                return None
                
            # Store original directory before changing
            self.original_dir = os.getcwd()
            
            # Log début d'exécution
            self._log(f"[{self.__class__.__name__}] 🚀 Démarrage Aider avec prompt: {prompt[:100]}...")
            
            # Use configured mission_dir directly
            try:
                # Validate mission directory
                if not self.mission_dir:
                    self._log(f"[{self.__class__.__name__}] ❌ No mission directory configured")
                    return None

                if not os.path.exists(self.mission_dir):
                    self._log(f"[{self.__class__.__name__}] ❌ Mission directory not found: {self.mission_dir}")
                    return None

                work_dir = PathManager.get_project_root()
                
                self._log(f"[{self.__class__.__name__}] 📂 Mission directory: {self.mission_dir}")
                self._log(f"[{self.__class__.__name__}] 📂 Working directory: {work_dir}")
                
            except Exception as e:
                self.logger.log(f"[{self.__class__.__name__}] ❌ Error getting paths: {str(e)}")
                return None

            try:
                os.chdir(self.mission_dir)
                self._log(f"[{self.__class__.__name__}] 📂 Changed to directory: {self.mission_dir}")

                # Build command with explicit paths and logging
                cmd = [
                    "aider",
                    "--model", "claude-3-5-haiku-20241022", # DON'T CHANGE ME gpt-4o-mini
                    "--yes-always",
                    "--cache-prompts",
                    "--no-pretty",
                    "--architect"
                ]
                
                self._log(f"[{self.__class__.__name__}] 🛠️ Commande Aider: {' '.join(cmd)}")
                
                # Add files with detailed logging
                files_added = []
                for file_path in self.mission_files:
                    try:
                        # Get relative path directly from mission_dir
                        rel_path = os.path.relpath(file_path, self.mission_dir)
                        
                        # Normalize path for consistency
                        normalized_path = os.path.normpath(rel_path)
                        
                        if os.path.exists(os.path.join(self.mission_dir, normalized_path)):
                            cmd.extend(["--file", normalized_path])
                            files_added.append(normalized_path)
                            self._log(f"[{self.__class__.__name__}] ➕ Added file: {normalized_path}")
                    except Exception as e:
                        self._log(f"[{self.__class__.__name__}] ❌ Error adding file {file_path}: {str(e)}")
                        continue

                # Log les fichiers ajoutés
                self._log(f"[{self.__class__.__name__}] 📄 Fichiers ajoutés: {files_added}")
                
                # Add the message/prompt
                cmd.extend(["--message", prompt])

                # Set environment variables for encoding
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                
                self._log(f"[{self.__class__.__name__}] 🚀 Lancement Aider...")
            
                # Validate command before execution
                try:
                    import shutil
                    aider_path = shutil.which('aider')
                    if not aider_path:
                        self._log(f"[{self.__class__.__name__}] ❌ Aider command not found in PATH", 'error')
                        return None
                        
                    self._log(f"[{self.__class__.__name__}] ✓ Found Aider at: {aider_path}", 'debug')
                    
                    # Test if we can access the mission directory
                    if not os.access(self.mission_dir, os.R_OK | os.W_OK):
                        self._log(
                            f"[{self.__class__.__name__}] ❌ Cannot access mission directory: {self.mission_dir}", 
                            'error'
                        )
                        return None
                        
                except Exception as e:
                    self._log(f"[{self.__class__.__name__}] ❌ Command validation failed: {str(e)}", 'error')
                    return None

                # Set timeout duration (5 minutes)
                TIMEOUT_SECONDS = 300

                # Execute Aider with output streaming
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Redirect stderr to stdout
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    env=env,
                    bufsize=1
                )

                # Initialize output collection
                output_lines = []
                error_detected = False
                
                # Read output while process is running
                while True:
                    try:
                        line = process.stdout.readline()
                        if not line and process.poll() is not None:
                            break
                            
                        line = line.rstrip()
                        if line:
                            # Handle Windows console warning
                            if "No Windows console found" in line:
                                self._log(
                                    f"[{self.__class__.__name__}] ⚠️ Windows console initialization warning:\n"
                                    f"This is a known issue and doesn't affect functionality.\n"
                                    f"Original message: {line}",
                                    'warning'
                                )
                                continue

                            # Commit type icons
                            COMMIT_ICONS = {
                                'feat': '✨',     # New feature
                                'fix': '🐛',      # Bug fix
                                'docs': '📚',     # Documentation
                                'style': '💎',    # Style/formatting
                                'refactor': '♻️',  # Refactoring
                                'perf': '⚡️',     # Performance
                                'test': '🧪',     # Tests
                                'build': '📦',    # Build/dependencies
                                'ci': '🔄',       # CI/CD
                                'chore': '🔧',    # Maintenance
                                'revert': '⏪',    # Revert changes
                            }

                            # Parse commit messages
                            if line.startswith("Commit ") and " " in line[7:]:
                                try:
                                    # Format: "Commit e7975b9 refactor: Remove web_instance..."
                                    commit_hash = line[7:].split()[0]  # Extract hash
                                    commit_type = line[7+len(commit_hash):].strip().split(":", 1)
                                    
                                    if len(commit_type) == 2:
                                        commit_category = commit_type[0].strip().lower()  # e.g. "refactor"
                                        commit_message = commit_type[1].strip()   # e.g. "Remove web_instance..."
                                        
                                        # Get appropriate icon or default to 🔨
                                        icon = COMMIT_ICONS.get(commit_category, '🔨')
                                        
                                        self._log(
                                            f"[{self.__class__.__name__}] {icon} Commit [{commit_category}] {commit_hash}: {commit_message}", 
                                            'success'
                                        )
                                    else:
                                        # No category, just message
                                        commit_message = line[7+len(commit_hash):].strip()
                                        self._log(
                                            f"[{self.__class__.__name__}] 🔨 Commit {commit_hash}: {commit_message}", 
                                            'success'
                                        )
                                        
                                except Exception as e:
                                    # Fallback if parsing fails
                                    self._log(f"[{self.__class__.__name__}] 🔨 {line}", 'success')
                            else:
                                # Handle non-commit lines
                                lower_line = line.lower()
                                is_error = any(err in lower_line for err in [
                                    'error', 'exception', 'failed', 'can\'t initialize'
                                ])
                                
                                if is_error:
                                    self._log(f"[{self.__class__.__name__}] ❌ {line}", 'error')
                                    error_detected = True
                                else:
                                    self._log(f"[{self.__class__.__name__}] 📝 {line}", 'info')
                            
                            output_lines.append(line)
                            
                    except Exception as e:
                        self._log(f"[{self.__class__.__name__}] Error reading output: {str(e)}")
                        continue

                # Get return code and check timeout
                try:
                    return_code = process.wait(timeout=TIMEOUT_SECONDS)
                except subprocess.TimeoutExpired:
                    process.kill()
                    self._log(
                        f"[{self.__class__.__name__}] ⚠️ Process timed out after {TIMEOUT_SECONDS} seconds", 
                        'warning'
                    )
                    return None
                
                # Get any remaining output
                try:
                    remaining_out, remaining_err = process.communicate(timeout=5)
                    if remaining_out:
                        for line in remaining_out.splitlines():
                            if line.strip():
                                print(f"[{self.name}] {line}")
                                output_lines.append(line)
                    if remaining_err:
                        for line in remaining_err.splitlines():
                            if line.strip():
                                print(f"[{self.name}] ⚠️ {line}")
                                output_lines.append(f"ERROR: {line}")
                except subprocess.TimeoutExpired:
                    process.kill()
                    self._log(f"[{self.__class__.__name__}] Process killed due to timeout")

                # Combine all output
                full_output = "\n".join(output_lines)

                # Add debug log for dataset processing start
                self._log(
                    f"[{self.__class__.__name__}] 🔄 Starting dataset processing:\n"
                    f"Return code: {return_code}\n"
                    f"Output length: {len(full_output) if full_output else 0} chars\n"
                    f"Dataset service available: {hasattr(self.web_instance, 'dataset_service')}\n"
                    f"Current directory: {os.getcwd()}",
                    'debug'
                )
                
                # Track modified files from output
                modified_files = set()
                for line in output_lines:
                    if "Wrote " in line and ".md" in line:
                        try:
                            modified_file = line.split("Wrote ")[1].split()[0]
                            modified_files.add(modified_file)
                        except:
                            pass

                # Si l'exécution est réussie, sauvegarder pour le fine-tuning
                if return_code == 0 and full_output:
                    try:
                        # Lire le contenu des fichiers modifiés
                        files_context = {}
                        for file_path in modified_files:
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    files_context[file_path] = f.read()
                            except Exception as e:
                                self._log(f"[{self.__class__.__name__}] Error reading modified file: {str(e)}")
                                continue

                        # Ajouter aussi les fichiers initiaux
                        for file_path in self.mission_files:
                            if file_path not in files_context:
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        files_context[file_path] = f.read()
                                except Exception as e:
                                    self._log(f"[{self.__class__.__name__}] Error reading original file: {str(e)}")
                                    continue

                        # S'assurer qu'il y a des fichiers à sauvegarder
                        if files_context:
                            # Create event loop if needed
                            try:
                                loop = asyncio.get_event_loop()
                            except RuntimeError:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)

                            # Dataset functionality disabled in CLI mode

                    except Exception as e:
                        self._log(
                            f"[{self.__class__.__name__}] ❌ Error processing dataset interaction: {str(e)}\n"
                            f"Traceback: {traceback.format_exc()}", 
                            'error'
                        )

                
                # Log completion status
                if return_code != 0 or error_detected:
                    self._log(
                        f"[{self.__class__.__name__}] ❌ Aider process failed (code: {return_code})\n"
                        f"Last few lines of output:\n" + 
                        "\n".join(output_lines[-5:]),  # Show last 5 lines
                        'error'
                    )
                    return None
                
                # Combine output
                full_output = "\n".join(output_lines)
                if not full_output.strip():
                    self._log(f"[{self.__class__.__name__}] ⚠️ No output from Aider", 'warning')
                    return None
                    
                self._log(f"[{self.__class__.__name__}] ✅ Aider completed successfully", 'success')
                
                # Track modified files from output
                modified_files = set()
                for line in output_lines:
                    if "Wrote " in line and ".md" in line:
                        try:
                            modified_file = line.split("Wrote ")[1].split()[0]
                            modified_files.add(modified_file)
                        except:
                            pass

                # If execution was successful, save for fine-tuning
                if return_code == 0 and full_output:
                    try:
                        # Read modified files content
                        files_context = {}
                        for file_path in modified_files:
                            try:
                                # Use relative path for reading
                                full_path = os.path.join(self.mission_dir, file_path)
                                if os.path.exists(full_path):
                                    with open(full_path, 'r', encoding='utf-8') as f:
                                        files_context[file_path] = f.read()
                            except Exception as e:
                                self.logger.log(f"Error reading modified file {file_path}: {str(e)}", 'error')
                                continue

                        # Add original files if not already included
                        for file_path in self.mission_files:
                            rel_path = os.path.relpath(file_path, self.mission_dir)
                            if rel_path not in files_context:
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        files_context[rel_path] = f.read()
                                except Exception as e:
                                    self.logger.log(f"Error reading original file {file_path}: {str(e)}", 'error')
                                    continue

                        # Only proceed if we have files to save
                        if files_context:
                            # Check dataset service availability silently
                            if (hasattr(self.web_instance, 'dataset_service') and 
                                self.web_instance.dataset_service and 
                                hasattr(self.web_instance.dataset_service, 'is_available') and 
                                self.web_instance.dataset_service.is_available()):
                                try:
                                    # Create event loop if needed
                                    try:
                                        loop = asyncio.get_event_loop()
                                    except RuntimeError:
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)

                                    # Add to dataset asynchronously
                                    loop.create_task(
                                        self.web_instance.dataset_service.add_interaction_async(
                                            prompt=prompt,
                                            files_context=files_context,
                                            aider_response=full_output
                                        )
                                    )
                                    self.logger.log(
                                        f"Added interaction to dataset with {len(files_context)} files", 
                                        'success'
                                    )
                                except Exception as e:
                                    self.logger.log(
                                        f"Error adding to dataset: {str(e)}\n"
                                        f"Traceback: {traceback.format_exc()}", 
                                        'error'
                                    )
                                finally:
                                    # Clean up if we created a new loop
                                    try:
                                        loop.close()
                                    except:
                                        pass

                    except Exception as e:
                        self._log(f"[{self.__class__.__name__}] Error saving to dataset: {str(e)}")

                # Return output if process succeeded
                if return_code == 0:
                    return full_output
                else:
                    self._log(f"[{self.__class__.__name__}] Process failed with code {return_code}")
                    return None

            finally:
                # Restore original directory in finally block
                try:
                    if self.original_dir:
                        os.chdir(self.original_dir)
                        self._log(f"[{self.__class__.__name__}] 📂 Restored directory: {self.original_dir}")
                except Exception as e:
                    self._log(f"[{self.__class__.__name__}] ❌ Error restoring directory: {str(e)}")
                    
        except Exception as e:
            self._log(f"[{self.__class__.__name__}] ❌ Error running Aider: {str(e)}")
            return None

    def list_files(self) -> None:
        """Liste tous les fichiers textuels dans le dossier de la mission"""
        try:
            # Use configured mission_dir directly
            if not self.mission_dir:
                self._log(f"[{self.__class__.__name__}] ❌ No mission directory configured")
                self.mission_files = {}
                return

            # Validate mission directory exists and is accessible
            if not os.path.exists(self.mission_dir):
                self._log(f"[{self.__class__.__name__}] ❌ Mission directory not found: {self.mission_dir}")
                self.mission_files = {}
                return

            if not os.access(self.mission_dir, os.R_OK | os.W_OK):
                self._log(f"[{self.__class__.__name__}] ❌ Insufficient permissions for: {self.mission_dir}")
                self.mission_files = {}
                return

            # Liste des extensions à inclure
            text_extensions = {'.md', '.txt', '.json', '.yaml', '.yml', '.py', '.js', '.html', '.css', '.sh'}
            
            # Log directory contents for debugging
            self._log(f"[{self.__class__.__name__}] 📂 Scanning directory: {self.mission_dir}")
            
            # Récupérer tous les fichiers textuels
            text_files = {}
            for root, dirs, filenames in os.walk(self.mission_dir):
                self._log(f"[{self.__class__.__name__}] 🔍 Scanning subdirectory: {root}")
                for filename in filenames:
                    if os.path.splitext(filename)[1].lower() in text_extensions:
                        file_path = os.path.join(root, filename)
                        text_files[file_path] = os.path.getmtime(file_path)
                        self._log(f"[{self.__class__.__name__}] ✓ Found file: {filename}")
        
            # Mettre à jour mission_files
            self.mission_files = text_files
            
            # Log final results
            self._log(f"[{self.__class__.__name__}] 📁 Found {len(self.mission_files)} files in {self.mission_dir}")
            for file in self.mission_files:
                rel_path = os.path.relpath(file, self.mission_dir)
                self._log(f"[{self.__class__.__name__}] 📄 {rel_path}")
                
        except Exception as e:
            self._log(f"[{self.__class__.__name__}] ❌ Error listing files: {str(e)}")
            self.mission_files = {}

    def get_prompt(self) -> str:
        """Get the current prompt content with caching"""
        try:
            if not self.prompt_file:
                return self.prompt  # Return default prompt if no file specified
                
            # Check cache first
            mtime = os.path.getmtime(self.prompt_file)
            if self.prompt_file in self._prompt_cache:
                cached_time, cached_content = self._prompt_cache[self.prompt_file]
                if cached_time == mtime:
                    return cached_content

            # Load from file if not in cache or cache invalid
            from utils.path_manager import PathManager
            try:
                prompts_dir = PathManager.get_prompts_path()
                prompt_path = os.path.join(prompts_dir, self.prompt_file)
                
                if os.path.exists(prompt_path):
                    with open(prompt_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self._prompt_cache[self.prompt_file] = (mtime, content)
                        return content
                else:
                    self._log(f"Prompt file not found: {self.prompt_file}")
                    return self.prompt  # Fallback to default prompt
            except Exception as e:
                self._log(f"Error accessing prompt file: {str(e)}")
                return self.prompt  # Fallback to default prompt
                
        except Exception as e:
            self._log(f"Error loading prompt: {str(e)}")
            return self.prompt  # Fallback to default prompt

    def save_prompt(self, content: str) -> bool:
        """Save new prompt content with validation"""
        try:
            if not self.prompt_file:
                self.logger("No prompt file configured")
                return False
                
            # Validate content
            if not content or not content.strip():
                raise ValueError("Prompt content cannot be empty")
                
            # Ensure prompts directory exists
            os.makedirs(os.path.dirname(self.prompt_file), exist_ok=True)
            
            # Save to temporary file first
            temp_file = f"{self.prompt_file}.tmp"
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                # Rename temp file to actual file (atomic operation)
                os.replace(temp_file, self.prompt_file)
                
                # Update instance prompt and clear cache
                self.prompt = content
                if self.prompt_file in self._prompt_cache:
                    del self._prompt_cache[self.prompt_file]
                    
                self._log(f"Prompt saved successfully to {self.prompt_file}")
                return True
                
            finally:
                # Clean up temp file if it exists
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
        except Exception as e:
            self._log(f"Error saving prompt: {str(e)}")
            return False

    def _load_prompt(self) -> Optional[str]:
        """Charge le prompt depuis le fichier avec cache"""
        try:
            if not self.prompt_file:
                return None
                
            # Vérifier le cache
            mtime = os.path.getmtime(self.prompt_file)
            if self.prompt_file in self._prompt_cache:
                cached_time, cached_content = self._prompt_cache[self.prompt_file]
                if cached_time == mtime:
                    return cached_content
                    
            # Charger et mettre en cache
            with open(self.prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self._prompt_cache[self.prompt_file] = (mtime, content)
            return content
            
        except Exception as e:
            self._log(f"Erreur chargement prompt: {e}")
            return None

    def cleanup(self):
        """Cleanup method to restore directory if needed"""
        try:
            if hasattr(self, 'original_dir') and self.original_dir:
                try:
                    os.chdir(self.original_dir)
                    self._log(f"[{self.__class__.__name__}] 📂 Restored directory during cleanup: {self.original_dir}")
                except Exception as e:
                    self._log(f"[{self.__class__.__name__}] ❌ Error restoring directory during cleanup: {str(e)}")
        except Exception as e:
            self._log(f"[{self.__class__.__name__}] ❌ Error in cleanup: {str(e)}")

    def stop(self):
        """Stop method to ensure cleanup"""
        try:
            # Call cleanup first
            self.cleanup()
            
            # Then handle regular stop logic
            self.running = False
            self._log(f"[{self.__class__.__name__}] 🛑 Agent stopped")
            
        except Exception as e:
            self._log(f"[{self.__class__.__name__}] ❌ Error stopping agent: {str(e)}")

    def run(self):
        """Main execution loop for the agent"""
        try:
            self._log(f"[{self.__class__.__name__}] 🚀 Starting agent run loop")
            
            while self.running:
                try:
                    # Check for shutdown signal
                    if hasattr(self.web_instance, 'agent_service') and \
                       self.web_instance.agent_service._shutting_down.is_set():
                        self._log(f"[{self.__class__.__name__}] Shutdown signal received")
                        break

                    # Use configured mission directory instead of checking current_mission
                    if not self.mission_dir:
                        self._log(f"[{self.__class__.__name__}] ❌ No mission directory configured")
                        time.sleep(60)
                        continue

                    # Validate mission directory
                    if not os.path.exists(self.mission_dir):
                        self._log(f"[{self.__class__.__name__}] ❌ Mission directory not found: {self.mission_dir}")
                        time.sleep(60)
                        continue
                        
                    if not os.access(self.mission_dir, os.R_OK | os.W_OK):
                        self._log(f"[{self.__class__.__name__}] ❌ Insufficient permissions on: {self.mission_dir}")
                        time.sleep(60)
                        continue

                    # Update file list with configured mission directory
                    self.list_files()
                    
                    # Get current prompt
                    prompt = self.get_prompt()
                    if not prompt:
                        self._log(f"[{self.__class__.__name__}] ⚠️ No prompt available, skipping run")
                        time.sleep(60)
                        continue
                        
                    # Run Aider with current prompt
                    result = self.run_aider(prompt)
                    
                    # Update state based on result
                    self.last_run = datetime.now()
                    if result:
                        self.last_change = datetime.now()
                        self.consecutive_no_changes = 0
                    else:
                        self.consecutive_no_changes += 1
                        
                    # Calculate and wait for next interval
                    interval = self.calculate_dynamic_interval()
                    time.sleep(interval)
                    
                except Exception as loop_error:
                    self._log(f"[{self.__class__.__name__}] ❌ Error in run loop: {str(loop_error)}")
                    if hasattr(self.web_instance, 'agent_service') and \
                       self.web_instance.agent_service._shutting_down.is_set():
                        break
                    time.sleep(5)  # Pause before retrying

            self._log(f"[{self.__class__.__name__}] Run loop ended")
            
        except Exception as e:
            self._log(f"[{self.__class__.__name__}] Critical error in run: {str(e)}")
            self.running = False
        finally:
            # Ensure cleanup happens
            self.cleanup()

    def _validate_run_conditions(self, prompt: str) -> bool:
        """Validate conditions before running Aider"""
        try:
            if not prompt or not prompt.strip():
                self._log(f"[{self.__class__.__name__}] ❌ Prompt vide", 'error')
                return False
                
            if not self.mission_dir:
                self._log(f"[{self.__class__.__name__}] ❌ Dossier mission non défini", 'error')
                return False
                
            if not os.path.exists(self.mission_dir):
                self._log(f"[{self.__class__.__name__}] ❌ Dossier mission non trouvé: {self.mission_dir}", 'error')
                return False
                
            if not self.mission_files:
                self._log(f"[{self.__class__.__name__}] ❌ Aucun fichier mission trouvé", 'warning')
                return False
                
            return True
            
        except Exception as e:
            self._log(f"[{self.__class__.__name__}] ❌ Erreur validation conditions: {str(e)}", 'error')
            return False

    def _build_prompt(self, context: dict = None) -> str:
        """
        Build the complete prompt with context.
        
        Args:
            context (dict, optional): Additional context to include in prompt
            
        Returns:
            str: Complete formatted prompt
        """
        try:
            # Get base prompt content
            prompt_content = self.get_prompt()
            if not prompt_content:
                raise ValueError("No prompt content available")
                
            # If no context provided, return base prompt
            if not context:
                return prompt_content
                
            # Format mission files info
            files_info = self._format_mission_files(context)
            
            # Add agent status info
            status_info = {
                'last_run': self.last_run.isoformat() if self.last_run else 'Never',
                'last_change': self.last_change.isoformat() if self.last_change else 'Never',
                'consecutive_no_changes': self.consecutive_no_changes,
                'current_interval': self.calculate_dynamic_interval()
            }
            
            # Combine all context
            full_context = {
                'files': files_info,
                'status': status_info,
                **context  # Include any additional context
            }
            
            # Format prompt with context
            return prompt_content.format(**full_context)
            
        except Exception as e:
            self.logger(f"Error building prompt: {str(e)}")
            return self.prompt  # Fallback to default prompt
    def _safe_log(self, message: str, level: str = 'info') -> None:
        """Thread-safe logging"""
        try:
            with self._log_lock:
                self.logger.log(message, level)
        except Exception as e:
            print(f"Logging error: {str(e)} - Message: {message}")  # Fallback
