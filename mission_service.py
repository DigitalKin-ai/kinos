import os
from datetime import datetime
from typing import List, Dict, Optional

class MissionService:
    def __init__(self):
        self.missions_dir = "missions"
        os.makedirs(self.missions_dir, exist_ok=True)

    def create_mission(self, name: str, description: str = None) -> Dict:
        """Create a new mission directory"""
        mission_dir = os.path.join(self.missions_dir, name)
        if os.path.exists(mission_dir):
            raise ValueError(f"Mission '{name}' already exists")
            
        os.makedirs(mission_dir)
        
        # Create default files
        for file_name in ["demande.md", "specifications.md", "management.md", 
                         "production.md", "evaluation.md", "suivi.md"]:
            with open(os.path.join(mission_dir, file_name), 'w', encoding='utf-8') as f:
                f.write(f"# {file_name[:-3].capitalize()}\n[Initial content]")
                
        # Return mission info
        return {
            'id': len(self.get_all_missions()),
            'name': name,
            'description': description,
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

    def get_all_missions(self) -> List[Dict]:
        """Get all missions by reading directories"""
        try:
            missions = []
            if os.path.exists(self.missions_dir):
                for mission_name in os.listdir(self.missions_dir):
                    mission_path = os.path.join(self.missions_dir, mission_name)
                    if os.path.isdir(mission_path):
                        mission = {
                            'id': len(missions) + 1,  # Simple incremental ID
                            'name': mission_name,
                            'description': '',
                            'status': 'active',
                            'created_at': datetime.fromtimestamp(os.path.getctime(mission_path)).isoformat(),
                            'updated_at': datetime.fromtimestamp(os.path.getmtime(mission_path)).isoformat()
                        }
                        missions.append(mission)
            return missions
        except Exception as e:
            print(f"Error getting missions: {e}")
            return []

    def get_mission(self, mission_id: int) -> Optional[Dict]:
        """Get a mission by ID"""
        missions = self.get_all_missions()
        for mission in missions:
            if mission['id'] == mission_id:
                # Add file paths
                mission_dir = os.path.join(self.missions_dir, mission['name'])
                mission['files'] = {
                    'demande': os.path.join(mission_dir, "demande.md"),
                    'specifications': os.path.join(mission_dir, "specifications.md"),
                    'management': os.path.join(mission_dir, "management.md"),
                    'production': os.path.join(mission_dir, "production.md"),
                    'evaluation': os.path.join(mission_dir, "evaluation.md"),
                    'suivi': os.path.join(mission_dir, "suivi.md")
                }
                return mission
        return None

    def update_mission(self, mission_id: int, name: str = None, 
                      description: str = None, status: str = None) -> Optional[Dict]:
        """Update mission metadata by updating directory timestamp"""
        try:
            mission = self.get_mission(mission_id)
            if not mission:
                return None
                
            mission_dir = os.path.join(self.missions_dir, mission['name'])
            
            # Update directory timestamp to reflect changes
            os.utime(mission_dir, None)
            
            # Return updated mission info
            return self.get_mission(mission_id)
            
        except Exception as e:
            print(f"Error updating mission: {e}")
            return None

    def save_mission_file(self, mission_id: int, file_type: str, content: str) -> bool:
        """Save content to a mission file"""
        try:
            mission = self.get_mission(mission_id)
            if not mission or file_type not in mission['files']:
                return False
                
            file_path = mission['files'][file_type]
            
            # Créer le répertoire de la mission s'il n'existe pas
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return True
            
        except Exception as e:
            print(f"Error saving mission file: {e}")
            return False

    def mission_exists(self, mission_name: str) -> bool:
        """Check if a mission directory exists"""
        return os.path.exists(os.path.join(self.missions_dir, mission_name))

    def delete_mission(self, mission_id: int) -> bool:
        """Delete a mission directory and all its files"""
        try:
            mission = self.get_mission(mission_id)
            if not mission:
                return False
                
            mission_dir = os.path.join(self.missions_dir, mission['name'])
            if os.path.exists(mission_dir):
                import shutil
                shutil.rmtree(mission_dir)
                return True
                
            return False
            
        except Exception as e:
            print(f"Error deleting mission: {e}")
            return False
