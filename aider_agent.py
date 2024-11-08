"""
AiderAgent - Agent générique utilisant Aider pour les modifications de fichiers
"""
from parallagon_agent import ParallagonAgent
import os
import subprocess
from typing import Dict, Optional

class AiderAgent(ParallagonAgent):
    """
    Agent utilisant Aider pour effectuer des modifications sur les fichiers.
    Chaque instance représente un rôle spécifique (specifications, production, etc.)
    mais partage la même logique d'interaction avec Aider.
    """
    
    def __init__(self, config: Dict):
        """Initialize the Aider agent with configuration."""
        super().__init__(config)
        
        # Validation de la configuration
        if "name" not in config:
            raise ValueError("Le nom de l'agent doit être spécifié")
        if "prompt" not in config:
            raise ValueError("Le prompt de l'agent doit être spécifié")
        if "mission_name" not in config:
            raise ValueError("Le nom de la mission doit être spécifié")
            
        self.name = config["name"]
        self.prompt = config["prompt"]
        self.prompt_file = config.get("prompt_file")
        self._prompt_cache = {}
        
        # Construire les chemins dans le dossier de la mission
        mission_dir = os.path.abspath(os.path.join("missions", config["mission_name"]))
        
        # S'assurer que le dossier de mission existe
        os.makedirs(mission_dir, exist_ok=True)
        
        # Utiliser le chemin fourni s'il est absolu, sinon le construire
        if os.path.isabs(config["file_path"]):
            self.file_path = config["file_path"]
        else:
            # Construire le chemin absolu pour le fichier principal
            self.file_path = os.path.join(mission_dir, os.path.basename(config["file_path"]))
        
        # Créer le fichier principal s'il n'existe pas
        if not os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write("")  # Créer un fichier vide
                self.logger(f"[{self.__class__.__name__}] ✓ Fichier principal créé: {self.file_path}")
            except Exception as e:
                self.logger(f"[{self.__class__.__name__}] ❌ Erreur création fichier: {str(e)}")
                raise

        # Initialize other_files and load content
        self.other_files = {}  # Initialize empty first
        self.list_files()  # Load all text files from mission directory
            
        self.logger(f"[{self.__class__.__name__}] Initialisé comme {self.name}")
        self.logger(f"[{self.__class__.__name__}] Dossier mission: {mission_dir}")
        self.logger(f"[{self.__class__.__name__}] Fichier principal: {self.file_path}")
        self.logger(f"[{self.__class__.__name__}] Fichiers secondaires: {list(self.other_files)}")

    def _run_aider(self, prompt: str) -> Optional[str]:
        """Exécute Aider avec le prompt donné"""
        try:
            self.logger(f"[{self.__class__.__name__}] Starting Aider run")
            self.logger(f"[{self.__class__.__name__}] Current file content length: {os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0}")
            
            # S'assurer que le fichier principal existe
            if not os.path.exists(self.file_path):
                self.logger(f"[{self.__class__.__name__}] ❌ Fichier principal non trouvé: {self.file_path}")
                # Créer le fichier s'il n'existe pas
                os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write("")  # Créer un fichier vide
                self.logger(f"[{self.__class__.__name__}] ✓ Fichier principal créé")

            # S'assurer que nous sommes dans le bon dossier de mission
            mission_dir = os.path.dirname(self.file_path)
            current_dir = os.getcwd()
            
            try:
                # Changer vers le dossier de la mission
                os.chdir(mission_dir)
                self.logger(f"[{self.__class__.__name__}] 📂 Changement vers le dossier: {mission_dir}")

                # Construire la commande avec des chemins relatifs au dossier de mission
                cmd = [
                    "aider",
                    "--model", "anthropic/claude-3-5-haiku-20241022",
                    "--no-git",
                    "--yes-always",
                    "--file", os.path.basename(self.file_path),  # Utiliser le nom de fichier relatif
                ]
                
                # Ajouter les fichiers à surveiller en chemins relatifs
                for file_path in self.other_files:
                    if os.path.exists(file_path):  # Vérifier que le fichier existe
                        cmd.extend(["--file", os.path.relpath(file_path, mission_dir)])
                    
                # Ajouter le message
                cmd.extend(["--message", self.prompt])
                
                # Logger la commande
                self.logger(f"[{self.__class__.__name__}] 🤖 Commande Aider:")
                self.logger(f"  Command: {' '.join(cmd)}")
                
                # Exécuter Aider
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate()
                
                # Logger la sortie
                if stdout:
                    self.logger(f"[{self.__class__.__name__}] ✓ Sortie Aider:\n{stdout}")
                if stderr:
                    self.logger(f"[{self.__class__.__name__}] ⚠️ Erreurs Aider:\n{stderr}")
                
                if process.returncode == 0:
                    # Si Aider a réussi, lire le nouveau contenu du fichier
                    with open(self.file_path, 'r', encoding='utf-8') as f:
                        new_content = f.read()
                    
                    # Notifier du changement via une requête à l'API
                    try:
                        # Construire les données de notification
                        file_name = os.path.basename(self.file_path)
                        panel_name = os.path.splitext(file_name)[0].capitalize()
                        
                        notification_data = {
                            'file_path': file_name,  # Juste le nom du fichier
                            'content': new_content,
                            'panel': panel_name,     # Nom du panneau (ex: "Specifications") 
                            'flash': True,
                            'type': 'info',
                            'message': f'Content updated in {panel_name}'
                        }
                        
                        # Log notification data for debugging
                        self.logger(f"Sending notification data: {notification_data}")
                        
                        # Faire la requête POST pour notifier du changement
                        import requests
                        response = requests.post(
                            'http://localhost:8000/api/notifications',  # Changement d'endpoint
                            json=notification_data
                        )
                        
                        # Log response details
                        self.logger(f"Notification response: {response.status_code}")
                        if response.status_code != 200:
                            self.logger(f"Response content: {response.text}")
                            
                        if response.status_code == 200:
                            self.logger(f"✓ Notification de changement envoyée pour {panel_name}")
                        else:
                            self.logger(f"❌ Erreur notification changement: {response.status_code}")
                            
                    except Exception as e:
                        self.logger(f"❌ Erreur envoi notification: {str(e)}")
                    
                    return stdout
                else:
                    self.logger(f"[{self.__class__.__name__}] ❌ Échec (code {process.returncode})")
                    return None
                
            finally:
                # Toujours revenir au dossier original
                os.chdir(current_dir)
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur exécution Aider: {str(e)}")
            return None

    def list_files(self) -> None:
        """
        Liste tous les fichiers textuels dans le dossier de la mission 
        et initialise other_files en excluant le fichier principal.
        """
        try:
            # Obtenir le dossier de la mission
            mission_dir = os.path.dirname(self.file_path)
            
            # Liste des extensions à inclure
            text_extensions = {'.md', '.txt', '.json', '.yaml', '.yml'}
            
            # Récupérer tous les fichiers textuels
            text_files = {}
            for file in os.listdir(mission_dir):
                file_path = os.path.join(mission_dir, file)
                # Vérifier si c'est un fichier et si l'extension est supportée
                if (os.path.isfile(file_path) and 
                    os.path.splitext(file)[1].lower() in text_extensions):
                    text_files[file_path] = os.path.getmtime(file_path)
            
            # Supprimer le fichier principal de la liste
            if self.file_path in text_files:
                del text_files[self.file_path]
                
            # Mettre à jour other_files
            self.other_files = text_files
            
            self.logger(f"[{self.__class__.__name__}] 📁 Fichiers trouvés: {len(self.other_files)}")
            for file in self.other_files:
                self.logger(f"[{self.__class__.__name__}] 📄 {os.path.basename(file)}")
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur listing fichiers: {str(e)}")
            self.other_files = {}  # Reset en cas d'erreur

    def get_prompt(self) -> str:
        """Get the current prompt content"""
        try:
            if not self.prompt_file:
                return self.prompt  # Return default prompt if no file specified
                
            # Try to load from file
            if os.path.exists(self.prompt_file):
                with open(self.prompt_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                self.logger(f"Prompt file not found: {self.prompt_file}")
                return self.prompt  # Fallback to default prompt
                
        except Exception as e:
            self.logger(f"Error loading prompt: {str(e)}")
            return self.prompt  # Fallback to default prompt

    def save_prompt(self, content: str) -> bool:
        """Save new prompt content"""
        try:
            if not self.prompt_file:
                self.logger("No prompt file configured")
                return False
                
            # Ensure prompts directory exists
            os.makedirs(os.path.dirname(self.prompt_file), exist_ok=True)
            
            # Save to file
            with open(self.prompt_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # Update instance prompt
            self.prompt = content
            
            # Clear cache
            if self.prompt_file in self._prompt_cache:
                del self._prompt_cache[self.prompt_file]
                
            self.logger(f"Prompt saved successfully to {self.prompt_file}")
            return True
            
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

    def _build_prompt(self, context: dict) -> str:
        """Charge et formate le prompt depuis le fichier"""
        try:
            prompt_template = self._load_prompt()
            if not prompt_template:
                return super()._build_prompt(context)
                
            return prompt_template.format(
                context=self._format_other_files(context)
            )
        except Exception as e:
            self.logger(f"Erreur chargement prompt: {e}")
            return super()._build_prompt(context)  # Fallback au prompt par défaut
