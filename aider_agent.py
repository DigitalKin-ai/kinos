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
import os
import subprocess
import time
import asyncio
from datetime import datetime
from typing import Dict, Optional

class AiderAgent(KinOSAgent):
    """
    Agent utilisant Aider pour effectuer des modifications sur les fichiers.
    Chaque instance représente un rôle spécifique (specifications, production, etc.)
    mais partage la même logique d'interaction avec Aider.
    """
    
    
    def _handle_agent_error(self, operation: str, error: Exception) -> None:
        """Centralized error handling for agent operations"""
        self._log(f"[{self.__class__.__name__}] ❌ Error in {operation}: {str(error)}")

    def __init__(self, config: Dict):
        # Validation de la configuration
        if "name" not in config:
            raise ValueError("Le nom de l'agent doit être spécifié")
            
        # Validate web_instance
        self.web_instance = config.get("web_instance")
        if not self.web_instance:
            raise ValueError("web_instance must be provided in config")
            
        # Add original_dir tracking
        self.original_dir = None
            
        # Initialize logger properly
        if hasattr(self.web_instance, 'logger'):
            self.logger = self.web_instance.logger
        else:
            from utils.logger import Logger
            self.logger = Logger()
            
        # Verify required services
        required_services = ['dataset_service', 'file_manager', 'mission_service']
        missing_services = [svc for svc in required_services 
                          if not hasattr(self.web_instance, svc)]
        
        if missing_services:
            self.logger.log(
                f"Missing required services: {missing_services}. "
                "Agent functionality may be limited.", 
                'warning'
            )
        
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

    def _run_aider(self, prompt: str) -> Optional[str]:
        """Execute Aider with given prompt and stream output."""
        try:
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
                
                self._log(f"[{self.__class__.__name__}] 📂 Dossier mission: {self.mission_dir}")
                self._log(f"[{self.__class__.__name__}] 📂 Dossier travail: {work_dir}")
                
            except Exception as e:
                self.logger.log(f"[{self.__class__.__name__}] ❌ Error getting paths: {str(e)}")
                return None

            try:
                os.chdir(self.mission_dir)  # Use configured mission_dir
                self._log(f"[{self.__class__.__name__}] 📂 Changed to directory: {self.mission_dir}")

                # Build command with explicit paths and logging
                cmd = [
                    "aider",
                    "--model", "claude-3-5-haiku-20241022", # DON'T CHANGE ME gpt-4o-mini
                    "--no-git",
                    "--yes-always",
                    "--cache-prompts",
                    "--restore-chat-history", "true",
                    "--no-pretty",
                    "--fancy-input", "false",
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
            
                # Execute Aider with output streaming
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    env=env,
                    bufsize=1
                )

                # Initialize output collection
                output_lines = []
                
                # Read output while process is running
                while True:
                    try:
                        # Check if process has finished
                        if process.poll() is not None:
                            break
                            
                        # Read stdout
                        stdout_line = process.stdout.readline()
                        if stdout_line:
                            line = stdout_line.strip()
                            if line:
                                print(f"[{self.name}] {line}")
                                output_lines.append(line)
                                
                        # Read stderr
                        stderr_line = process.stderr.readline()
                        if stderr_line:
                            line = stderr_line.strip()
                            if line:
                                print(f"[{self.name}] ⚠️ {line}")
                                output_lines.append(f"ERROR: {line}")
                                
                    except Exception as e:
                        self._log(f"[{self.__class__.__name__}] Error reading output: {str(e)}")
                        continue

                # Get final return code
                return_code = process.poll()
                
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

                            # Check dataset service availability
                            if hasattr(self.web_instance, 'dataset_service'):
                                dataset_service = self.web_instance.dataset_service
                                if dataset_service and dataset_service.is_available():
                                    try:
                                        # Create event loop if needed
                                        try:
                                            loop = asyncio.get_event_loop()
                                        except RuntimeError:
                                            loop = asyncio.new_event_loop()
                                            asyncio.set_event_loop(loop)

                                        # Add to dataset asynchronously
                                        loop.create_task(
                                            dataset_service.add_interaction_async(
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
                                        self.logger.log(f"Error adding to dataset: {str(e)}", 'error')
                                else:
                                    self.logger.log("Dataset service not available or properly initialized", 'warning')
                            else:
                                self.logger.log("Dataset service not found on web instance", 'warning')

                    except Exception as e:
                        self._log(f"[{self.__class__.__name__}] Error saving to dataset: {str(e)}")

                # Return output if process succeeded
                if return_code == 0:
                    return full_output
                else:
                    self._log(f"[{self.__class__.__name__}] Process failed with code {return_code}")
                    return None
                
                # Créer des buffers séparés pour la sortie d'Aider et les fichiers modifiés
                aider_output_buffer = []
                modified_files = set()
                
                # Stream output in real-time
                while True:
                    # Read stdout
                    stdout_line = process.stdout.readline()
                    if stdout_line:
                        line = stdout_line.rstrip()
                        print(f"[{self.name}] {line}")  # Print to main output
                        aider_output_buffer.append(line)
                        
                        # Détecter les fichiers modifiés dans la sortie
                        if "Wrote " in line and ".md" in line:
                            try:
                                modified_file = line.split("Wrote ")[1].split()[0]
                                modified_files.add(modified_file)
                            except:
                                pass
                        
                    # Read stderr
                    stderr_line = process.stderr.readline()
                    if stderr_line:
                        line = stderr_line.rstrip()
                        print(f"[{self.name}] ⚠️ {line}")  # Print errors to main output
                        aider_output_buffer.append(f"ERROR: {line}")
                    
                    # Check if process has finished
                    if process.poll() is not None:
                        break
                
                # Get any remaining output
                stdout, stderr = process.communicate()
                if stdout:
                    for line in stdout.splitlines():
                        print(f"[{self.name}] {line}")
                        aider_output_buffer.append(line)
                if stderr:
                    for line in stderr.splitlines():
                        print(f"[{self.name}] ⚠️ {line}")
                        aider_output_buffer.append(f"ERROR: {line}")
                
                # Combine all output
                full_output = "\n".join(aider_output_buffer)
                
                # If execution was successful, save for fine-tuning
                if process.returncode == 0 and full_output:
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
                            # Check dataset service availability
                            if hasattr(self.web_instance, 'dataset_service'):
                                dataset_service = self.web_instance.dataset_service
                                if dataset_service and dataset_service.is_available():
                                    try:
                                        # Create event loop if needed
                                        try:
                                            loop = asyncio.get_event_loop()
                                        except RuntimeError:
                                            loop = asyncio.new_event_loop()
                                            asyncio.set_event_loop(loop)

                                        # Add to dataset asynchronously
                                        loop.create_task(
                                            dataset_service.add_interaction_async(
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
                                        self.logger.log(f"Error adding to dataset: {str(e)}", 'error')
                                else:
                                    self.logger.log("Dataset service not available or properly initialized", 'warning')
                            else:
                                self.logger.log("Dataset service not found on web instance", 'warning')

                    except Exception as e:
                        self.logger.log(f"Error processing files for dataset: {str(e)}", 'error')

                    # Continue with normal operation
                    return full_output

                else:
                    self.logger.log(f"Aider process failed with code {process.returncode}", 'error')
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
            # Use configured mission_dir directly instead of checking current_mission
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
                    time.sleep(60)  # Wait before retrying
                    
        except Exception as e:
            self._log(f"[{self.__class__.__name__}] 🔥 Critical error in run: {str(e)}")
            self.running = False

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
        """Build the complete prompt with context"""
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
