import os
from typing import Dict, List, Optional
from datetime import datetime
from utils.logger import Logger
from utils.decorators import safe_operation
from utils.logger import Logger
from utils.exceptions import AgentError
from utils.path_manager import PathManager

class MissionService:

    def __init__(self):
        """Initialize mission service"""
        self.missions_dir = PathManager.get_mission_path("")  # Get root missions dir
        self.logger = Logger()  # Initialize logger
        self._missions_cache = None
        self._last_scan = 0
        self.scan_interval = 5  # Seconds between directory scans
        
    def _normalize_mission_path(self, path: str) -> str:
        """Normalise le chemin de mission pour éviter les duplications"""
        # Convertir en chemin absolu
        normalized = os.path.abspath(path)
        
        # Séparer le chemin en composants
        parts = normalized.split(os.sep)
        
        # Trouver toutes les occurrences de "missions"
        mission_indices = [i for i, part in enumerate(parts) if part.lower() == "missions"]
        
        # S'il y a plusieurs "missions", garder seulement la dernière occurrence
        if len(mission_indices) > 1:
            # Reconstruire le chemin en gardant tout jusqu'à la dernière occurrence de "missions"
            last_missions_index = mission_indices[-1]
            normalized = os.path.join(*parts[:last_missions_index], *parts[last_missions_index+1:])
            
        return normalized

    def _ensure_missions_dir(self):
        """Find and set the missions directory path"""
        try:
            self.missions_dir = PathManager.get_mission_path("")
            self.logger.log(f"Found missions directory: {self.missions_dir}", 'info')
            return True
        except Exception as e:
            self.logger.log(f"Error finding missions directory: {e}", 'error')
            raise

    def get_all_missions(self):
        """Get all missions"""
        try:
            return self._scan_missions()
        except Exception as e:
            self.logger.log(f"Error getting missions: {str(e)}", 'error')
            return []

    def mission_exists(self, mission_id: int) -> bool:
        """Check if a mission exists by ID"""
        try:
            missions = self._scan_missions()
            return any(mission['id'] == mission_id for mission in missions)
        except Exception as e:
            self.logger.log(f"Error checking mission existence: {str(e)}", 'error')
            return False

    def get_mission(self, mission_id: int) -> Optional[Dict]:
        """Get a specific mission by ID with better error handling"""
        try:
            missions = self._scan_missions()
            
            if not missions:
                self.logger.log("No missions found", 'warning')
                return None

            # Find mission by ID
            mission = next((m for m in missions if m['id'] == mission_id), None)
            
            if not mission:
                self.logger.log(f"Mission {mission_id} not found", 'warning')
                return None

            # Normalize path
            mission['path'] = self._normalize_mission_path(
                os.path.join(self.missions_dir, mission['name'])
            )

            # Verify directory exists and is accessible
            if not os.path.exists(mission['path']):
                self.logger.log(f"Mission directory not found: {mission['path']}", 'warning')
                return None
                
            if not os.access(mission['path'], os.R_OK | os.W_OK):
                self.logger.log(f"Insufficient permissions on: {mission['path']}", 'warning')
                return None

            # Initialize empty files dictionary
            mission['files'] = {}

            return mission
            
        except Exception as e:
            self.logger.log(f"Error getting mission: {str(e)}", 'error')
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

    def _normalize_mission_name(self, mission_name: str) -> str:
        """Normalize mission name for filesystem use"""
        normalized = mission_name.replace("'", "_")
        normalized = normalized.replace('"', "_")
        normalized = normalized.replace(" ", "_")
        return normalized

    def create_mission(self, name: str, description: str = None) -> Optional[Dict]:
        """Create a new mission with only demande.md initially"""
        try:
            # Validate mission name
            if not name or not name.strip():
                raise ValueError("Mission name cannot be empty")
                
            # Normalize name for filesystem
            normalized_name = self._normalize_mission_name(name)
            
            
            # Use PathManager to get mission directory path
            mission_dir = PathManager.get_mission_path(normalized_name)
            
            # Create directory
            os.makedirs(mission_dir, exist_ok=True)
            
            # Return mission data
            return {
                'id': len(self.get_all_missions()) + 1, 
                'name': name,
                'path': mission_dir,
                'status': 'active',
                'description': description,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.log(f"Error creating mission: {e}", 'error')
            return None


    def _get_initial_content(self, file_type: str) -> str:
        """Get initial content for a specific file type from templates"""
        try:
            # Construire le chemin vers le fichier template
            template_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # Remonte au root du projet
                'templates',
                'initial_content',
                f'{file_type}.md'
            )
            
            # Vérifier si le fichier existe
            if not os.path.exists(template_path):
                self.logger.log(f"Template file not found: {template_path}", 'warning')
                # Retourner un contenu par défaut si le template n'existe pas
                return f"# {file_type.capitalize()}\n\nInitial content for {file_type}"
                
            # Lire le contenu du template
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return content
            
        except Exception as e:
            self.logger.log(f"Error loading template for {file_type}: {str(e)}", 'error')
            # Retourner un contenu par défaut en cas d'erreur
            return f"# {file_type.capitalize()}\n\nInitial content for {file_type}"

    def _scan_missions(self) -> List[Dict]:
        """Scan missions directory and return mission data"""
        try:
            missions = []
            mission_id = 1  # Start with ID 1
            
            # Get all mission directories
            mission_dirs = []
            for item in os.listdir(self.missions_dir):
                mission_path = os.path.join(self.missions_dir, item)
                if os.path.isdir(mission_path):
                    mission_dirs.append((item, mission_path))
            
            # Sort by creation time to maintain consistent IDs
            mission_dirs.sort(key=lambda x: os.path.getctime(x[1]))
            
            # Process each mission directory
            for mission_name, mission_path in mission_dirs:
                # Create mission object with sequential ID
                mission = {
                    'id': mission_id,
                    'name': mission_name,
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
            self.logger.log(f"Error scanning missions directory: {e}", 'error')
            return []

    def get_mission_by_name(self, mission_name):
        """
        Récupère une mission par son nom
        
        Args:
            mission_name (str): Nom de la mission
        
        Returns:
            dict: Informations de la mission ou None
        """
        missions = self._scan_missions()
        return next((mission for mission in missions if mission['name'] == mission_name), None)
