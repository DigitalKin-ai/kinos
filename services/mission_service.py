import os
from typing import Dict, List, Optional
from datetime import datetime
from utils.logger import Logger
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
        "suivi.md",
        "documentation.md",
        "duplication.md",
        "tests.md",
        "redaction.md"
    ]

    def __init__(self):
        """Initialize mission service with base directory"""
        self.missions_dir = "missions" 
        self.logger = Logger()  # Initialize logger
        self._ensure_missions_dir()
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
            # Chercher d'abord dans le répertoire courant
            if os.path.exists("missions"):
                self.missions_dir = self._normalize_mission_path("missions")
                self.logger.log(f"Found missions directory: {self.missions_dir}", level='info')
                return True

            # Si non trouvé, chercher dans le répertoire parent
            parent_missions = self._normalize_mission_path(os.path.join(os.path.dirname(__file__), "..", "missions"))
            if os.path.exists(parent_missions):
                self.missions_dir = parent_missions
                self.logger.log(f"Found missions directory: {self.missions_dir}", level='info')
                return True

            # Si toujours pas trouvé, chercher dans le répertoire utilisateur
            user_missions = self._normalize_mission_path(os.path.expanduser(os.path.join("~", "parallagon", "missions")))
            if os.path.exists(user_missions):
                self.missions_dir = user_missions
                self.logger.log(f"Found missions directory: {self.missions_dir}", level='info')
                return True

            # Si aucun dossier missions n'est trouvé, lever une exception
            raise ValueError("No missions directory found")

        except Exception as e:
            self.logger.log(f"Error finding missions directory: {e}", level='error')
            raise

    def get_all_missions(self):
        """Get all missions"""
        try:
            return self._scan_missions()
        except Exception as e:
            self.logger.log(f"Error getting missions: {str(e)}", level='error')
            return []

    def mission_exists(self, mission_id: int) -> bool:
        """Check if a mission exists by ID"""
        try:
            missions = self._scan_missions()
            return any(mission['id'] == mission_id for mission in missions)
        except Exception as e:
            self.logger.log(f"Error checking mission existence: {str(e)}", level='error')
            return False

    def get_mission(self, mission_id: int) -> Optional[Dict]:
        """Get a specific mission by ID with better error handling"""
        try:
            # Log le chemin du dossier missions
            # self.logger.log(f"Looking for mission {mission_id} in {self.missions_dir}", level='debug')
            
            missions = self._scan_missions()
            
            # Log les missions trouvées
            # self.logger.log(f"Found missions: {[m['name'] for m in missions]}", level='debug')
            
            # Check if missions list is empty
            if not missions:
                self.logger.log("No missions found, creating default mission", level='info')
                default_mission = self.create_mission("Mission_1", "Default mission")
                if default_mission:
                    missions = [default_mission]
                else:
                    raise Exception("Failed to create default mission")
            
            # Find mission by ID
            mission = next((m for m in missions if m['id'] == mission_id), None)
            
            if mission:
                # Normaliser le chemin
                mission['path'] = self._normalize_mission_path(
                    os.path.join(self.missions_dir, mission['name'])
                )
            
            if not mission:
                self.logger.log(f"Mission {mission_id} not found", level='warning')
                return None
                
            # Add file paths
            mission['files'] = {
                name: os.path.join(mission['path'], f"{name}.md")
                for name in ['demande', 'specifications', 'management',
                            'production', 'evaluation', 'suivi']
            }
            
            # self.logger.log(f"Found mission: {mission['name']} (ID: {mission_id})", level='debug')
            return mission
            
        except Exception as e:
            self.logger.log(f"Error getting mission: {str(e)}", level='error')
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
        """Create a new mission and ensure its directory exists"""
        try:
            # Validate mission name
            if not name or not name.strip():
                raise ValueError("Mission name cannot be empty")
                
            # Normalize name for filesystem
            normalized_name = self._normalize_mission_name(name)
            
            # Construire le chemin ABSOLU du dossier mission
            mission_dir = os.path.abspath(os.path.join(self.missions_dir, normalized_name))
            
            # Normaliser le chemin pour éviter toute duplication
            mission_dir = self._normalize_mission_path(mission_dir)
            
            # Log pour debug
            self.logger.log(f"Creating mission in: {mission_dir}", level='debug')
            
            # Create required files with initial content
            for filename in self.REQUIRED_FILES:
                # Utiliser un chemin absolu pour le fichier
                file_path = os.path.abspath(os.path.join(mission_dir, filename))
                if not os.path.exists(file_path):
                    # Créer le dossier parent avec chemin absolu
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        initial_content = self._get_initial_content(filename.replace('.md', ''))
                        f.write(initial_content)
                    self.logger.log(f"Created file: {filename}", level='debug')

            # Return mission data with original and normalized names
            mission_data = {
                'id': len(self.get_all_missions()) + 1,
                'name': name,  # Original name
                'normalized_name': normalized_name,  # Add normalized name
                'path': mission_dir,
                'status': 'active',
                'description': description,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.logger.log(f"Created mission: {name}", level='success')
            return mission_data
            
        except Exception as e:
            self.logger.log(f"Error creating mission: {e}", level='error')
            return None

    def ensure_mission_files(self, mission_name: str) -> bool:
        """Create standard files for a mission if they don't exist"""
        try:
            # Utiliser un chemin absolu pour le dossier mission
            mission_dir = os.path.abspath(os.path.join(self.missions_dir, mission_name))
            
            # Create each required file if it doesn't exist
            for filename in self.REQUIRED_FILES:
                # Utiliser un chemin absolu pour le fichier
                file_path = os.path.abspath(os.path.join(mission_dir, filename))
                if not os.path.exists(file_path):
                    # Créer le dossier parent avec chemin absolu
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        content = self._get_initial_content(filename.replace('.md', ''))
                        f.write(content)
            return True
        except Exception as e:
            self.logger.log(f"Error ensuring mission files: {e}", level='error')
            return False

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
                self.logger.log(f"Template file not found: {template_path}", level='warning')
                # Retourner un contenu par défaut si le template n'existe pas
                return f"# {file_type.capitalize()}\n\nInitial content for {file_type}"
                
            # Lire le contenu du template
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return content
            
        except Exception as e:
            self.logger.log(f"Error loading template for {file_type}: {str(e)}", level='error')
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
                # Check if any required files exist
                has_files = any(
                    os.path.exists(os.path.join(mission_path, req_file))
                    for req_file in self.REQUIRED_FILES
                )
                
                if has_files:
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
                    
                    # Ensure required files exist
                    self.ensure_mission_files(mission_name)
            
            # Log scanned missions
            # self.logger.log(f"Scanned missions: {[m['name'] for m in missions]}", level='debug')
            # self.logger.log(f"Mission IDs: {[m['id'] for m in missions]}", level='debug')
            
            return missions
            
        except Exception as e:
            self.logger.log(f"Error scanning missions directory: {e}", level='error')
            return []
