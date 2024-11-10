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
        """
        Execute Aider with given prompt.
        Only works with existing files, doesn't create new ones.
        """
        try:
            # Construire le chemin du fichier principal
            main_file = f"{self.role}.md"
            main_file_path = os.path.join(self.mission_dir, main_file)

            # Verify if main file exists
            if not os.path.exists(main_file_path):
                self.logger.log(f"Main file not found: {main_file_path}", level='warning')
                return None

            # Obtenir le dossier de mission
            current_dir = os.getcwd()
            
            try:
                # Changer vers le dossier de la mission
                os.chdir(self.mission_dir)
                self.logger(f"[{self.__class__.__name__}] 📂 Changement vers le dossier: {self.mission_dir}")

                # Utiliser uniquement les noms de fichiers (pas les chemins)
                main_file = os.path.basename(main_file_path)
                
                # Construire la commande avec chemins relatifs
                cmd = [
                    "aider",
                    "--model", "claude-3-5-haiku-20241022",
                    "--no-git",
                    "--yes-always",
                    "--file", main_file  # Utiliser juste le nom du fichier
                ]
                
                # Ajouter les autres fichiers (chemins relatifs)
                for file_path in self.mission_files:
                    rel_path = os.path.relpath(file_path, self.mission_dir)
                    if os.path.exists(rel_path):  # Vérifier le chemin relatif
                        cmd.extend(["--file", rel_path])
                        
                # Ajouter le message
                cmd.extend(["--message", self.prompt])
                
                # Logger la commande
                self.logger(f"[{self.__class__.__name__}] 🤖 Commande Aider :")
        
                # Exécuter Aider avec timeout et gestion d'encodage
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
        
                try:
                    stdout, stderr = process.communicate(timeout=600)
                except subprocess.TimeoutExpired:
                    process.kill()
                    self.logger(f"[{self.__class__.__name__}] ❌ Timeout exécution Aider")
                    time.sleep(min(300, 2 ** self.consecutive_no_changes * 30))
                    return None
                
                # Logger la sortie
                if stdout:
                    self.logger(f"[{self.__class__.__name__}] ✅ Sortie Aider:\n{stdout}")
                if stderr:
                    self.logger(f"[{self.__class__.__name__}] ⚠️ Erreurs Aider:\n{stderr}")
                
                if process.returncode == 0:
                    # Lire le contenu mis à jour (chemin relatif)
                    with open(main_file, 'r', encoding='utf-8') as f:
                        new_content = f.read()
                    
                    # Notifier du changement
                    try:
                        panel_name = os.path.splitext(main_file)[0].capitalize()
                        success = self.web_instance.notification_service.handle_content_change(
                            file_path=main_file,
                            content=new_content,
                            panel_name=panel_name,
                            flash=True
                        )
                        if success:
                            self.logger(f"✓ Notification sent for {panel_name}")
                        else:
                            self.logger(f"❌ Failed to send notification for {panel_name}")
                    except Exception as e:
                        self.logger(f"❌ Error sending notification: {str(e)}")
                    
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
        et initialise mission_files.
        """
        try:
            # Obtenir le dossier de la mission
            mission_dir = os.path.dirname(self.file_path)
            
            # Liste des extensions à inclure
            text_extensions = {'.md', '.txt', '.json', '.yaml', '.yml', '.py', '.js', '.html' '.css', '.sh'}
            
            # Récupérer tous les fichiers textuels
            text_files = {}
            for file in os.listdir(mission_dir):
                file_path = os.path.join(mission_dir, file)
                # Vérifier si c'est un fichier et si l'extension est supportée
                if (os.path.isfile(file_path) and 
                    os.path.splitext(file)[1].lower() in text_extensions):
                    text_files[file_path] = os.path.getmtime(file_path)
                
            # Mettre à jour mission_files
            self.mission_files = text_files
            
            self.logger(f"[{self.__class__.__name__}] 📁 Fichiers trouvés: {len(self.mission_files)}")
            for file in self.mission_files:
                self.logger(f"[{self.__class__.__name__}] 📄 {os.path.basename(file)}")
                
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur listing fichiers: {str(e)}")
            self.mission_files = {}  # Reset en cas d'erreur

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
                context=self._format_mission_files(context)
            )
        except Exception as e:
            self.logger(f"Erreur chargement prompt: {e}")
            return super()._build_prompt(context)  # Fallback au prompt par défaut
