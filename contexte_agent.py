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
        """Analyse optimisée de la pertinence d'un fichier"""
        try:
            # Limiter la taille du fichier lu
            MAX_SIZE = 100_000  # 100KB
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(MAX_SIZE)
                
            # Construire un prompt plus concis
            prompt = f"""Évaluez la pertinence (0-1):
Tâche: {current_task[:500]}
Fichier: {content[:1000]}
Répondre uniquement avec le score."""

            response = self._get_llm_response({"prompt": prompt})
            return float(response.strip())
            
        except Exception as e:
            self.logger(f"❌ Erreur d'analyse pour {file_path}: {e}")
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

    def _filter_relevance(self, scored_files: list, threshold: float = 0.5, max_files: int = 10) -> list:
        """Filtre les fichiers selon leur pertinence"""
        filtered = [(path, score) for path, score in scored_files if score >= threshold]
        filtered.sort(key=lambda x: x[1], reverse=True)
        return filtered[:max_files]

    def determine_actions(self) -> None:
        """Logique principale de l'agent"""
        try:
            self.logger(f"[{self.__class__.__name__}] Analyse du contexte...")
            
            # 1. Scanner uniquement les fichiers pertinents
            available_files = [f for f in self._scan_directory(os.getcwd()) 
                             if any(f.endswith(ext) for ext in ['.py', '.md', '.txt', '.html', '.css', '.js'])]

            # 2. Obtenir la tâche actuelle de manière plus efficace
            current_task = self._get_current_task()
            if not current_task.strip():
                self.logger(f"[{self.__class__.__name__}] Pas de tâche active")
                return

            # 3. Évaluer la pertinence avec un cache
            scored_files = []
            for file_path in available_files:
                cache_key = f"{file_path}_{hash(current_task)}"
                if hasattr(self, '_relevance_cache') and cache_key in self._relevance_cache:
                    score = self._relevance_cache[cache_key]
                else:
                    score = self._analyze_relevance(file_path, current_task)
                    if not hasattr(self, '_relevance_cache'):
                        self._relevance_cache = {}
                    self._relevance_cache[cache_key] = score
                scored_files.append((file_path, score))

            # 4. Filtrer et sélectionner les fichiers
            selected_files = [f[0] for f in self._filter_relevance(scored_files)]

            # 5. Mettre à jour uniquement si changement
            if set(selected_files) != self.current_context:
                self.current_context = set(selected_files)
                self._update_context_file(selected_files)
                self.logger(f"[{self.__class__.__name__}] ✓ Contexte mis à jour avec {len(selected_files)} fichiers")

        except Exception as e:
            self.logger(f"[{self.__class__.__name__}] ❌ Erreur: {str(e)}")
    def _clean_relevance_cache(self):
        """Nettoie périodiquement le cache de pertinence"""
        if hasattr(self, '_relevance_cache'):
            # Garder seulement les 1000 entrées les plus récentes
            cache_items = sorted(self._relevance_cache.items(), 
                               key=lambda x: x[1]['timestamp'])
            self._relevance_cache = dict(cache_items[-1000:])
