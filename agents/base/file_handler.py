"""File operations and monitoring"""
import os
from typing import Dict, Optional
from utils.logger import Logger
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

class FileHandler:
    """Handles file operations and monitoring"""
    def __init__(self, mission_dir: str, logger: Logger):
        self.mission_dir = mission_dir
        self.logger = logger
        self.mission_files = {}

    def list_files(self) -> Dict[str, float]:
        try:
            from services import init_services
            services = init_services(None)
            team_service = services['team_service']
            
            # Find agent's team
            agent_name = None  # Will be replaced with actual agent name
            agent_team = None
            for team in team_service.team_types:
                if agent_name in team.get('agents', []):
                    agent_team = team['id']
                    break

            # Search paths using team_types directory
            team_dir = os.path.join('team_types', agent_team) if agent_team else None
            search_paths = [self.mission_dir]
            if team_dir and os.path.exists(team_dir):
                search_paths.append(team_dir)

            # Charger les modèles d'exclusion
            ignore_patterns = self._load_ignore_patterns()
            spec = PathSpec.from_lines(GitWildMatchPattern, ignore_patterns) if ignore_patterns else None

            # Extensions de fichiers texte
            text_extensions = {'.md', '.txt', '.json', '.yaml', '.yml', '.py', '.js', '.html', '.css', '.sh'}
            text_files = {}

            for base_path in search_paths:
                for root, _, filenames in os.walk(base_path):
                    for filename in filenames:
                        if os.path.splitext(filename)[1].lower() in text_extensions:
                            file_path = os.path.join(root, filename)
                            rel_path = os.path.relpath(file_path, base_path)
                            
                            # Ignorer les fichiers correspondant aux modèles
                            if spec and spec.match_file(rel_path):
                                continue
                            
                            # Priorité aux fichiers spécifiques de l'agent/équipe
                            if agent_team and agent_name:
                                specific_patterns = [
                                    f"team_{agent_team}_{agent_name}_{filename}",
                                    f"{agent_name}_{filename}",
                                    f"team_{agent_team}_{filename}"
                                ]
                                if any(pattern in filename for pattern in specific_patterns):
                                    text_files[file_path] = os.path.getmtime(file_path)
                            
                            # Ajouter les fichiers génériques si pas déjà ajouté
                            if file_path not in text_files:
                                text_files[file_path] = os.path.getmtime(file_path)

            self.mission_files = text_files
            return text_files

        except Exception as e:
            self.logger.log(f"Error listing files: {str(e)}", 'error')
            return {}

    def _load_ignore_patterns(self) -> list:
        """Load patterns from .gitignore and .aiderignore"""
        patterns = []
        for ignore_file in ['.gitignore', '.aiderignore']:
            try:
                ignore_path = os.path.join(self.mission_dir, ignore_file)
                if os.path.exists(ignore_path):
                    with open(ignore_path, 'r', encoding='utf-8') as f:
                        file_patterns = [p.strip() for p in f.readlines() 
                                       if p.strip() and not p.startswith('#')]
                        patterns.extend(file_patterns)
            except Exception as e:
                self.logger.log(f"Error reading {ignore_file}: {str(e)}", 'warning')
        return patterns

    def validate_paths(self) -> bool:
        """Validate all required paths"""
        try:
            if not os.path.exists(self.mission_dir):
                self.logger.log(f"Mission directory not found: {self.mission_dir}", 'error')
                return False
                
            if not os.access(self.mission_dir, os.R_OK | os.W_OK):
                self.logger.log(f"Insufficient permissions on: {self.mission_dir}", 'error')
                return False
                
            return True
            
        except Exception as e:
            self.logger.log(f"Error validating paths: {str(e)}", 'error')
            return False
