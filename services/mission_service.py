import os
from typing import Dict, List, Optional
from datetime import datetime
from utils.decorators import safe_operation
from utils.logger import Logger
from utils.exceptions import AgentError

class MissionService:
    REQUIRED_FILES = [
        "demande.md",
        "specifications.md", 
        "management.md",
        "production.md",
        "evaluation.md",
        "suivi.md"
    ]

    def __init__(self):
        """Initialize mission service with base directory"""
        self.missions_dir = "missions" 
        self._ensure_missions_dir()
        self._missions_cache = None
        self._last_scan = 0
        self.scan_interval = 5  # Seconds between directory scans

    def _ensure_missions_dir(self):
        """Ensure missions directory exists"""
        try:
            if not os.path.exists(self.missions_dir):
                os.makedirs(self.missions_dir)
                print(f"Created missions directory: {self.missions_dir}")
        except Exception as e:
            print(f"Error creating missions directory: {e}")
            raise

    def get_all_missions(self):
        """Get all missions"""
        try:
            return self._scan_missions()
        except Exception as e:
            print(f"Error getting missions: {str(e)}")
            return []

    def get_mission(self, mission_id: int) -> Optional[Dict]:
        """Get a specific mission by ID"""
        missions = self.get_all_missions()
        for mission in missions:
            if mission['id'] == mission_id:
                # Add file paths
                mission['files'] = {
                    name: os.path.join(mission['path'], f"{name}.md")
                    for name in ['demande', 'specifications', 'management', 
                               'production', 'evaluation', 'suivi']
                }
                return mission
        return None

    def ensure_mission_directory(self, mission_name: str) -> bool:
        """Create mission directory if it doesn't exist"""
        try:
            mission_dir = os.path.join(self.missions_dir, mission_name)
            os.makedirs(mission_dir, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating mission directory: {e}")
            return False

    def create_mission(self, name: str, description: str = None) -> Optional[Dict]:
        """Create a new mission and ensure its directory exists"""
        try:
            # Validate mission name
            if not name or not name.strip():
                raise ValueError("Mission name cannot be empty")

            # Create mission directory
            if not self.ensure_mission_directory(name):
                raise RuntimeError("Failed to create mission directory")

            # Ensure required files exist
            if not self.ensure_mission_files(name):
                raise RuntimeError("Failed to create mission files")

            # Return mission data
            return {
                'id': len(self.get_all_missions()) + 1,
                'name': name,
                'path': os.path.join(self.missions_dir, name),
                'status': 'active',
                'description': description,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error creating mission: {e}")
            return None

    def ensure_mission_files(self, mission_name: str) -> bool:
        """Create standard files for a mission if they don't exist"""
        try:
            mission_dir = os.path.join(self.missions_dir, mission_name)
            
            # Create each required file if it doesn't exist
            for filename in self.REQUIRED_FILES:
                file_path = os.path.join(mission_dir, filename)
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        # Get initial content based on file type
                        content = self._get_initial_content(filename.replace('.md', ''))
                        f.write(content)
            return True
        except Exception as e:
            print(f"Error ensuring mission files: {e}")
            return False

    def _get_initial_content(self, file_type: str) -> str:
        """Get initial content for a specific file type"""
        content_map = {
            'demande': '# Nouvelle Demande\n\nDécrivez votre demande ici...',
            'specifications': '# Spécifications\n\n## Vue d\'ensemble\n\n## Fonctionnalités\n\n## Contraintes',
            'management': '# Gestion de Projet\n\n## État Actuel\n\n## Prochaines Étapes\n\n## Risques',
            'production': '# Production\n\n## Code Source\n\n## Tests\n\n## Documentation',
            'evaluation': '# Évaluation\n\n## Tests Effectués\n\n## Résultats\n\n## Recommandations',
            'suivi': '# Suivi\n\n## Historique\n\n## Décisions\n\n## Métriques'
        }
        return content_map.get(file_type, '')

    def _scan_missions(self) -> List[Dict]:
        """Scan missions directory and return mission data"""
        try:
            missions = []
            mission_id = 1
            
            for item in os.listdir(self.missions_dir):
                mission_path = os.path.join(self.missions_dir, item)
                if not os.path.isdir(mission_path):
                    continue
                    
                # Check if any required files exist
                has_files = any(
                    os.path.exists(os.path.join(mission_path, req_file))
                    for req_file in self.REQUIRED_FILES
                )
                
                if has_files:
                    mission = {
                        'id': mission_id,  # Incrément séquentiel des IDs
                        'name': item,
                        'path': mission_path,
                        'status': 'active',
                        'created_at': datetime.fromtimestamp(
                            os.path.getctime(mission_path)
                        ).isoformat(),
                        'updated_at': datetime.fromtimestamp(
                            os.path.getmtime(mission_path)
                        ).isoformat()
                    }
                    missions.append(mission)
                    mission_id += 1
                    
            return missions
            
        except Exception as e:
            print(f"Error scanning missions directory: {e}")
            return []
