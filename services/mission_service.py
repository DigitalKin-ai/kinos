import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from utils.logger import Logger
from utils.path_manager import PathManager

class MissionService:
    """Service for managing missions"""
    
    def __init__(self):
        """Initialize mission service"""
        self.missions_dir = PathManager.get_mission_path("")  # Get root missions dir
        self.logger = Logger()  # Initialize logger
        self._missions_cache = None
        self._last_scan = 0
        self.scan_interval = 5  # Seconds between directory scans
        self.currentMission = None
        self.missions = []

    def select_mission(self, mission_id: int) -> Optional[Dict[str, Any]]:
        """
        Select a mission as current
        
        Args:
            mission_id: ID of the mission to select
            
        Returns:
            dict: Selected mission data or None if not found
        """
        try:
            # Validate mission_id
            if not isinstance(mission_id, (int, str)):
                raise ValueError("Invalid mission ID type")
            
            # Get the mission
            mission = self.get_mission(mission_id)
            if not mission:
                self.logger.log(f"Mission not found: {mission_id}", "error")
                return None
                
            # Update current mission
            self.currentMission = mission
            
            # Log success
            self.logger.log(f"Selected mission: {mission.get('name', mission_id)}", "info")
            
            return {
                **mission,
                'selected_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
        except Exception as e:
            self.logger.log(f"Error selecting mission: {str(e)}", "error")
            raise

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

            return mission
            
        except Exception as e:
            self.logger.log(f"Error getting mission: {str(e)}", 'error')
            return None

    def get_current_mission(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected mission"""
        return self.currentMission

    def get_all_missions(self) -> List[Dict[str, Any]]:
        """Get all missions"""
        try:
            return self._scan_missions()
        except Exception as e:
            self.logger.log(f"Error getting missions: {str(e)}", 'error')
            return []

    def _normalize_mission_path(self, path: str) -> str:
        """Normalize mission path to avoid duplications"""
        normalized = os.path.abspath(path)
        parts = normalized.split(os.sep)
        mission_indices = [i for i, part in enumerate(parts) if part.lower() == "missions"]
        
        if len(mission_indices) > 1:
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

    def _normalize_mission_name(self, mission_name: str) -> str:
        """Normalize mission name for filesystem use"""
        normalized = mission_name.replace("'", "_")
        normalized = normalized.replace('"', "_")
        normalized = normalized.replace(" ", "_")
        return normalized

    def create_mission(self, name: str, description: str = None) -> Optional[Dict]:
        """Create a new mission"""
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
            
            # Create mission data
            mission = {
                'id': len(self.get_all_missions()) + 1,
                'name': name,
                'path': mission_dir,
                'status': 'active',
                'description': description,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Add to in-memory list
            self.missions.append(mission)
            
            return mission
            
        except Exception as e:
            self.logger.log(f"Error creating mission: {e}", 'error')
            return None

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

    def get_mission_by_name(self, mission_name: str) -> Optional[Dict]:
        """Get a mission by name"""
        missions = self._scan_missions()
        return next((mission for mission in missions if mission['name'] == mission_name), None)
