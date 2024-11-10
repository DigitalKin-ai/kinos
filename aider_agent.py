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
from agents.kinos_agent import KinOSAgent
import os
import subprocess
import time
from typing import Dict, Optional

class AiderAgent(KinOSAgent):
    """
    Agent utilisant Aider pour effectuer des modifications sur les fichiers.
    Chaque instance représente un rôle spécifique (specifications, production, etc.)
    mais partage la même logique d'interaction avec Aider.
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        # Validation de la configuration
        if "name" not in config:
            raise ValueError("Le nom de l'agent doit être spécifié")
        if "prompt" not in config:
            raise ValueError("Le prompt de l'agent doit être spécifié")
        if "mission_name" not in config:
            raise ValueError("Le nom de la mission doit être spécifié")
        if "web_instance" not in config:
            raise ValueError("web_instance manquant dans la configuration")
            
        self.name = config["name"]
        self.web_instance = config["web_instance"]
        self.prompt = config["prompt"]
        self.prompt_file = config.get("prompt_file")
        self._prompt_cache = {}
        
        # Initialize watched files list
        self.watched_files = []

        self.logger(f"[{self.__class__.__name__}] Initialisé comme {self.name}")

    def _validate_mission_directory(self) -> bool:
        """Vérifie que le dossier de mission est valide et accessible"""
        try:
            if not os.path.exists(self.mission_dir):
                self.logger(f"[{self.__class__.__name__}] ❌ Dossier mission non trouvé: {self.mission_dir}")
                return False
                
            if not os.access(self.mission_dir, os.R_OK | os.W_OK):
                self.logger(f"[{self.__class__.__name__}] ❌ Permissions insuffisantes sur: {self.mission_dir}")
                return False
                
            self.logger(f"[{self.__class__.__name__}] ✓ Dossier mission valide: {self.mission_dir}")
            return True
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur validation dossier: {str(e)}")
            return False

    def _run_aider(self, prompt: str) -> Optional[str]:
        """Execute Aider with given prompt."""
        try:
            current_dir = os.getcwd()
            
            # Verify mission directory exists
            if not os.path.exists(self.mission_dir):
                self.logger(f"[{self.__class__.__name__}] ❌ Mission directory not found: {self.mission_dir}")
                return None

            try:
                os.chdir(self.mission_dir)
                self.logger(f"[{self.__class__.__name__}] 📂 Changed to directory: {self.mission_dir}")

                # Build command with explicit paths and logging
                cmd = [
                    "aider",
                    "--model", "claude-3-5-sonnet-20241022", # instead of claude-3-5-haiku-20241022
                    "--no-git",
                    "--yes-always",
                    "--cache-prompts"
                ]
                
                # Add files with detailed logging
                files_added = []
                for file_path in self.mission_files:
                    rel_path = os.path.relpath(file_path, self.mission_dir)
                    if os.path.exists(rel_path):
                        cmd.extend(["--file", rel_path])
                        files_added.append(rel_path)
                        
                # Add the message/prompt
                cmd.extend(["--message", prompt])
                
                # Log complete command
                self.logger(f"[{self.__class__.__name__}] 🤖 Running Aider command:")
                #self.logger(f"[{self.__class__.__name__}] Command: {' '.join(cmd)}")
                #self.logger(f"[{self.__class__.__name__}] Files: {files_added}")
                #self.logger(f"[{self.__class__.__name__}] Prompt: {prompt[:100]}...")
                
                # Set environment variables for encoding
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
            
                # Execute Aider with timeout and UTF-8 encoding
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    env=env
                )
                
                stdout, stderr = process.communicate(timeout=600)
                
                # Log output
                if stdout:
                    self.logger(f"[{self.__class__.__name__}] ✅ Aider output:\n{stdout}")
                if stderr:
                    self.logger(f"[{self.__class__.__name__}] ⚠️ Aider errors:\n{stderr}")
                
                return stdout if process.returncode == 0 else None
                
            finally:
                os.chdir(current_dir)
                    
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Error running Aider: {str(e)}")
            return None

    def list_files(self) -> None:
        """
        Liste tous les fichiers textuels dans le dossier de la mission COURANTE 
        et initialise mission_files.
        """
        try:
            # Vérifier que le dossier mission existe et est valide
            if not os.path.exists(self.mission_dir):
                self.logger(f"[{self.__class__.__name__}] ❌ Mission directory not found: {self.mission_dir}")
                self.mission_files = {}
                return

            # Liste des extensions à inclure
            text_extensions = {'.md', '.txt', '.json', '.yaml', '.yml', '.py', '.js', '.html', '.css', '.sh'}
            
            # Récupérer tous les fichiers textuels UNIQUEMENT dans le dossier de la mission courante
            text_files = {}
            for root, _, filenames in os.walk(self.mission_dir):
                # Vérifier que nous sommes toujours dans le dossier de la mission
                if not root.startswith(self.mission_dir):
                    continue
                    
                for filename in filenames:
                    if os.path.splitext(filename)[1].lower() in text_extensions:
                        file_path = os.path.join(root, filename)
                        # Ne garder que les fichiers qui sont dans le dossier de la mission
                        if os.path.commonpath([file_path, self.mission_dir]) == self.mission_dir:
                            text_files[file_path] = os.path.getmtime(file_path)
            
            # Mettre à jour mission_files
            self.mission_files = text_files
            
            self.logger(f"[{self.__class__.__name__}] 📁 Fichiers trouvés dans {self.mission_dir}: {len(self.mission_files)}")
            for file in self.mission_files:
                rel_path = os.path.relpath(file, self.mission_dir)
                self.logger(f"[{self.__class__.__name__}] 📄 {rel_path}")
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur listing fichiers: {str(e)}")
            self.mission_files = {}  # Reset en cas d'erreur

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
            if os.path.exists(self.prompt_file):
                with open(self.prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self._prompt_cache[self.prompt_file] = (mtime, content)
                    return content
            else:
                self.logger(f"Prompt file not found: {self.prompt_file}")
                return self.prompt  # Fallback to default prompt
                
        except Exception as e:
            self.logger(f"Error loading prompt: {str(e)}")
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
                    
                self.logger(f"Prompt saved successfully to {self.prompt_file}")
                return True
                
            finally:
                # Clean up temp file if it exists
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
        except Exception as e:
            self.logger(f"Error saving prompt: {str(e)}")
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
            self.logger(f"Erreur chargement prompt: {e}")
            return None

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
