import os
from typing import Dict, List, Optional
from datetime import datetime
from utils.decorators import safe_operation

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
                    
            return missions
            
        except Exception as e:
            print(f"Error scanning missions directory: {e}")
            return []
