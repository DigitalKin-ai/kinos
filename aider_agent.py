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
        self.prompt_file = config.get("prompt_file")
        self._prompt_cache = {}
        
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

    def _get_aider_instructions(self, prompt: str) -> Optional[str]:
        """Obtient les instructions pour Aider via GPT"""
        try:
            system_prompt = f"""Vous êtes {self.role}. 
Générez des instructions claires pour l'outil Aider qui modifiera le fichier {os.path.basename(self.file_path)}.
Les instructions doivent être précises et spécifier exactement quels changements effectuer.

Format attendu:
1. Listez les modifications à faire
2. Utilisez des références exactes au contenu existant
3. Décrivez le nouveau contenu à insérer
4. Restez factuel et direct"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger(f"Erreur génération instructions Aider: {str(e)}")
            return None

    def _run_aider(self, prompt: str) -> Optional[str]:
        """Exécute Aider avec le prompt donné"""
        try:
            # Obtenir les instructions pour Aider
            aider_instructions = self._get_aider_instructions(prompt)
            if not aider_instructions:
                return None

            # Construire la commande avec les fichiers à surveiller
            read_files = []
            for file in self.watch_files:
                read_files.extend(["--read", file])

            # Construire la commande Aider
            cmd = [
                "aider",
                "--model", "haiku",
                "--no-git",
                "--yes-always",
                "--file", self.file_path,
                *read_files,
                "--message", aider_instructions
            ]
            
            # Logger la commande complète
            self.logger(f"[{self.__class__.__name__}] 🤖 Commande Aider:")
            self.logger(f"  Command: {' '.join(cmd)}")
            self.logger(f"  Instructions: {aider_instructions}")
            
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
            
            if process.returncode != 0:
                self.logger(f"[{self.__class__.__name__}] ❌ Échec (code {process.returncode})")
                return None
                
            return stdout
            
        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur exécution Aider: {str(e)}")
            return None

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
            
    def _validate_content(self, content: str) -> bool:
        """Validate content before writing"""
        try:
            # Basic structure validation
            if not content.strip():
                return False
                
            # Check for required sections based on agent type
            required_sections = {
                'SpecificationsAgent': ['État Actuel', 'Signaux'],
                'ProductionAgent': ['État Actuel', 'Contenu Principal'],
                'ManagementAgent': ['État Actuel', 'TodoList', 'Actions Réalisées'],
                'EvaluationAgent': ['Évaluations en Cours', 'Vue d\'Ensemble']
            }
            
            agent_type = self.__class__.__name__
            if agent_type in required_sections:
                for section in required_sections[agent_type]:
                    if f"# {section}" not in content:
                        self.logger(f"Missing required section: {section}")
                        return False
                        
            return True
            
        except Exception as e:
            self.logger(f"Error validating content: {str(e)}")
            return False
