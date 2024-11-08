import os
from datetime import datetime
from typing import List, Dict, Optional

class MissionService:
    """Service for managing missions"""
    
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
        if not os.path.exists(self.missions_dir):
            os.makedirs(self.missions_dir)

    def _scan_missions(self) -> List[Dict]:
        """Scan missions directory and return mission data"""
        missions = []
        mission_id = 1
        
        try:
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
                        'id': mission_id,
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
                    
        except Exception as e:
            print(f"Error scanning missions directory: {e}")
            
        return missions

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

    def create_mission(self, name, description=None):
        """Create a new mission"""
        try:
            mission_dir = os.path.join(self.missions_dir, name)
            if os.path.exists(mission_dir):
                raise ValueError(f"Mission '{name}' already exists")
                
            os.makedirs(mission_dir)
            
            # Create required files
            for filename in self.REQUIRED_FILES:
                file_path = os.path.join(mission_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("")
                    
            # Force cache refresh
            self._missions_cache = None
            
            # Return new mission data
            missions = self.get_all_missions()
            return next((m for m in missions if m['name'] == name), None)
            
        except Exception as e:
            print(f"Error creating mission: {str(e)}")
            raise

    def mission_exists(self, name: str) -> bool:
        """Check if a mission exists"""
        return os.path.exists(os.path.join(self.missions_dir, name))
