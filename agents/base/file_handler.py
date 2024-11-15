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
        """List and track mission files"""
        try:
            if not os.path.exists(self.mission_dir):
                self.logger.log(f"Mission directory not found: {self.mission_dir}", 'error')
                return {}

            # Récupérer le nom de l'agent
            from services import init_services
            services = init_services(None)
            team_service = services['team_service']
            
            # Trouver l'équipe de l'agent
            agent_name = None
            agent_team = None
            for team in team_service.predefined_teams:
                if agent_name in team.get('agents', []):
                    agent_team = team['id']
                    break

            # Load ignore patterns
            ignore_patterns = self._load_ignore_patterns()
            spec = PathSpec.from_lines(GitWildMatchPattern, ignore_patterns) if ignore_patterns else None

            # Track text files
            text_extensions = {'.md', '.txt', '.json', '.yaml', '.yml', '.py', '.js', '.html', '.css', '.sh'}
            text_files = {}

            for root, _, filenames in os.walk(self.mission_dir):
                for filename in filenames:
                    if os.path.splitext(filename)[1].lower() in text_extensions:
                        file_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(file_path, self.mission_dir)
                        
                        # Skip if matches ignore patterns
                        if spec and spec.match_file(rel_path):
                            continue
                        
                        # Priorité aux fichiers spécifiques à l'agent/équipe
                        if agent_team and agent_name:
                            # Vérifier les noms de fichiers spécifiques
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
