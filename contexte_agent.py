"""
ContexteAgent - Agent responsable de la sélection contextuelle des fichiers pertinents
"""
import os
import fnmatch
from typing import List, Dict
from parallagon_agent import ParallagonAgent
import git

class ContexteAgent(ParallagonAgent):
    """
    Agent gérant la sélection intelligente du contexte pour les autres agents.
    
    Responsabilités:
    - Scanner les fichiers du projet
    - Filtrer selon .gitignore
    - Analyser la pertinence
    - Maintenir une liste de 5-10 fichiers les plus pertinents
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.current_context = set()  # Fichiers actuellement sélectionnés
        self.repo = git.Repo(os.getcwd())
        
    def _is_ignored(self, file_path: str) -> bool:
        """Vérifie si un fichier est ignoré par git"""
        try:
            return self.repo.ignored(file_path)
        except Exception as e:
            self.logger(f"Erreur lors de la vérification gitignore: {e}")
            return False
            
    def _scan_directory(self, directory: str) -> List[str]:
        """Scan récursif du répertoire en respectant .gitignore"""
        relevant_files = []
        
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                # Ignorer les fichiers .git et ceux matchant .gitignore
                if not self._is_ignored(file_path) and '.git' not in file_path:
                    relevant_files.append(file_path)
                    
        return relevant_files

    def _analyze_relevance(self, file_path: str, current_task: str) -> float:
        """Analyse la pertinence d'un fichier pour la tâche en cours"""
        try:
            # Lire le contenu du fichier
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Construire le prompt pour l'analyse
            prompt = f"""Évaluez la pertinence de ce fichier pour la tâche en cours.

Tâche actuelle:
{current_task}

Contenu du fichier:
{content[:1000]}  # Limiter pour l'API

Retournez un score de pertinence entre 0 et 1, où:
0 = Non pertinent
1 = Très pertinent

Répondez uniquement avec le score numérique."""

            # Obtenir le score via LLM
            response = self._get_llm_response({"prompt": prompt})
            return float(response.strip())
            
        except Exception as e:
            self.logger(f"Erreur d'analyse pour {file_path}: {e}")
            return 0.0

    def _get_current_task(self) -> str:
        """Extrait la tâche en cours depuis demande.md"""
        try:
            with open('demande.md', 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            self.logger(f"Erreur lecture demande.md: {e}")
            return ""

    def _update_context_file(self, selected_files: List[str]) -> None:
        """Met à jour le fichier contexte.md avec les fichiers sélectionnés"""
        try:
            content = f"""# Contexte
[timestamp: {self._get_timestamp()}]

## Fichiers Pertinents Sélectionnés
"""
            for file in selected_files:
                content += f"\n### {os.path.basename(file)}\n"
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    content += f"```\n{file_content}\n```\n"
                except Exception as e:
                    content += f"[Erreur lecture: {str(e)}]\n"
                    
            self.write_file(content)
            
        except Exception as e:
            self.logger(f"Erreur mise à jour contexte.md: {e}")

    def determine_actions(self) -> None:
        """Logique principale de l'agent"""
        try:
            # 1. Obtenir la tâche actuelle
            current_task = self._get_current_task()
            if not current_task:
                return

            # 2. Scanner les fichiers disponibles
            available_files = self._scan_directory(os.getcwd())

            # 3. Évaluer la pertinence de chaque fichier
            scored_files = []
            for file_path in available_files:
                score = self._analyze_relevance(file_path, current_task)
                scored_files.append((file_path, score))

            # 4. Sélectionner les 5-10 fichiers les plus pertinents
            scored_files.sort(key=lambda x: x[1], reverse=True)
            selected_files = [f[0] for f in scored_files[:10] if f[1] > 0.5]

            # 5. Mettre à jour le contexte si changement
            if set(selected_files) != self.current_context:
                self.current_context = set(selected_files)
                self._update_context_file(selected_files)
                self.logger("Contexte mis à jour avec nouveaux fichiers pertinents")

        except Exception as e:
            self.logger(f"Erreur dans determine_actions: {e}")
