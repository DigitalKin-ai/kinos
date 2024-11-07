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
        super().__init__(config)
        
        # Validation de la configuration
        if "role" not in config:
            raise ValueError("Le rôle de l'agent doit être spécifié")
        if "aider_prompt" not in config:
            raise ValueError("Le prompt Aider doit être spécifié")
            
        self.role = config["role"]
        self.aider_prompt = config["aider_prompt"]
        
        # Configuration des chemins
        if not os.path.isabs(config["file_path"]):
            config["file_path"] = os.path.abspath(config["file_path"])
        self.file_path = config["file_path"]
        
        # Créer le dossier parent si nécessaire
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        # Convertir les watch_files en chemins absolus
        if "watch_files" in config:
            self.watch_files = [
                os.path.abspath(f) if not os.path.isabs(f) else f
                for f in config["watch_files"]
            ]
            
        self.logger(f"[{self.__class__.__name__}] Initialisé comme {self.role}")

    def _run_aider(self, prompt: str) -> Optional[str]:
        """
        Exécute Aider avec le prompt donné
        """
        try:
            # Construire la commande Aider
            cmd = [
                "aider",
                "--model", "gpt-4",
                "--no-git",
                "--yes",  # Auto-accept changes
                self.file_path,
                *self.watch_files
            ]
            
            # Exécuter Aider
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Envoyer le prompt
            stdout, stderr = process.communicate(input=prompt)
            
            if process.returncode != 0:
                self.logger(f"[{self.__class__.__name__}] ❌ Erreur Aider: {stderr}")
                return None
                
            return stdout
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur exécution Aider: {str(e)}")
            return None

    def determine_actions(self) -> None:
        """
        Détermine et exécute les actions nécessaires via Aider
        """
        try:
            self.logger(f"[{self.__class__.__name__}] Analyse du contenu...")
            
            # Construire le contexte
            context = {
                "role": self.role,
                "current": self.current_content,
                "other_files": self.other_files
            }
            
            # Construire le prompt complet
            full_prompt = f"{self.aider_prompt}\n\nContexte actuel:\n{self._format_other_files(context)}"
            
            # Exécuter Aider
            result = self._run_aider(full_prompt)
            
            if result:
                self.logger(f"[{self.__class__.__name__}] ✓ Modifications effectuées")
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur: {str(e)}")
