"""File operations and monitoring"""
import os
import os
from typing import Dict, Optional, List
from utils.logger import Logger
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

class FileHandler:
    """Handles file operations and monitoring"""
    def __init__(self, mission_dir: str, logger: Logger):
        self.mission_dir = mission_dir
        self.logger = logger
        self.mission_files = {}

    def _detect_team_directories(self) -> List[str]:
        """
        Détecte dynamiquement les répertoires d'équipes
        
        Returns:
            Liste des chemins des répertoires d'équipes
        """
        try:
            current_dir = os.getcwd()
            team_dirs = [
                os.path.join(current_dir, d) 
                for d in os.listdir(current_dir) 
                if d.startswith('team_') and os.path.isdir(os.path.join(current_dir, d))
            ]
            return team_dirs
        except Exception as e:
            self.logger.log(f"Erreur de détection des répertoires d'équipes : {str(e)}", 'error')
            return []

    def list_files(self) -> Dict[str, float]:
        try:
            # Détecter dynamiquement les répertoires d'équipes
            search_paths = [self.mission_dir] + self._detect_team_directories()
            
            # Load ignore patterns
            ignore_patterns = self._load_ignore_patterns()
            spec = PathSpec.from_lines(GitWildMatchPattern, ignore_patterns) if ignore_patterns else None

            # Extensions of text files to track
            text_extensions = {'.md', '.txt', '.json', '.yaml', '.yml', '.py', '.js', '.html', '.css', '.sh'}
            text_files = {}

            for base_path in search_paths:
                for root, _, filenames in os.walk(base_path):
                    for filename in filenames:
                        if os.path.splitext(filename)[1].lower() in text_extensions:
                            file_path = os.path.join(root, filename)
                            rel_path = os.path.relpath(file_path, base_path)
                            
                            # Skip ignored files
                            if spec and spec.match_file(rel_path):
                                continue
                            
                            text_files[file_path] = os.path.getmtime(file_path)

            return text_files

        except Exception as e:
            self.logger.log(f"Erreur de listage des fichiers : {str(e)}", 'error')
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
