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
        """
        Initialize the Aider agent with configuration.
        
        Args:
            config (Dict): Configuration dictionary containing:
                - anthropic_api_key: API key for Anthropic
                - openai_api_key: API key for OpenAI
                - file_path: Path to main file
                - prompt_file: Path to prompt file (optional)
                - name: Agent name
                - mission_name: Current mission name
        """
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
        mission_dir = os.path.join("missions", config["mission_name"])
        
        # S'assurer que le chemin de fichier est dans le dossier de mission
        self.file_path = os.path.join(
            mission_dir, 
            os.path.basename(config["file_path"])
        )
        
        # Créer le dossier de mission si nécessaire
        os.makedirs(mission_dir, exist_ok=True)

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
                    "--model", "haiku",
                    "--no-git",
                    "--yes-always",
                    "--file", os.path.basename(self.file_path),  # Utiliser le nom de fichier relatif
                ]
                
                # Ajouter les fichiers à surveiller en chemins relatifs
                for file_path in self.other_files:
                    cmd.extend(["--file", os.path.relpath(file_path, mission_dir)])
                    
                # Ajouter le message
                cmd.extend(["--message", self.prompt])
                
                # Logger la commande
                self.logger(f"[{self.__class__.__name__}] 🤖 Commande Aider:")
                self.logger(f"  Command: {' '.join(cmd)}")
                self.logger(f"  Instructions: {self.prompt}")
                
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
                        # Construire l'URL relative au fichier modifié
                        file_name = os.path.basename(self.file_path)
                        panel_name = os.path.splitext(file_name)[0].capitalize()
                        
                        # Faire la requête POST pour notifier du changement
                        import requests
                        response = requests.post(
                            'http://localhost:8000/api/content/change',
                            json={
                                'file_path': self.file_path,
                                'content': new_content,
                                'panel_name': panel_name,
                                'flash': True
                            }
                        )
                        
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
