import os
from datetime import datetime
from typing import List, Dict, Optional

class MissionService:
    def __init__(self):
        """Initialize the mission service"""
        self.missions_dir = "missions"
        os.makedirs(self.missions_dir, exist_ok=True)

    REQUIRED_FILES = [
        "demande.md",
        "specifications.md", 
        "management.md",
        "production.md",
        "evaluation.md",
        "suivi.md"
    ]

    def get_all_missions(self) -> List[Dict]:
        """Get all missions by reading directories"""
        missions = []
        try:
            # Vérifier et créer le dossier missions si nécessaire
            if not os.path.exists(self.missions_dir):
                os.makedirs(self.missions_dir)
                return missions

            # Scanner uniquement le premier niveau du dossier missions
            for item in os.listdir(self.missions_dir):
                mission_path = os.path.join(self.missions_dir, item)
                
                # Ignorer les non-dossiers
                if not os.path.isdir(mission_path):
                    continue

                # Vérifier si au moins un fichier requis existe
                if any(os.path.exists(os.path.join(mission_path, req_file)) 
                      for req_file in self.REQUIRED_FILES):
                    
                    mission = {
                        'id': len(missions) + 1,
                        'name': item,
                        'description': '',
                        'status': 'active',
                        'created_at': datetime.fromtimestamp(
                            os.path.getctime(mission_path)
                        ).isoformat(),
                        'updated_at': datetime.fromtimestamp(
                            os.path.getmtime(mission_path)
                        ).isoformat()
                    }
                    missions.append(mission)

        except Exception as e:
            print(f"Error scanning missions: {str(e)}")
            
        return missions

    def create_mission(self, name: str, description: str = None) -> Dict:
        """Create a new mission directory"""
        mission_dir = os.path.join(self.missions_dir, name)
        if os.path.exists(mission_dir):
            raise ValueError(f"Mission '{name}' already exists")
            
        os.makedirs(mission_dir)
        
        # Créer les fichiers requis
        for filename in self.REQUIRED_FILES:
            file_path = os.path.join(mission_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("")
                
        return {
            'id': len(self.get_all_missions()),
            'name': name,
            'description': description,
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

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

    def mission_exists(self, mission_name: str) -> bool:
        """Check if a mission directory exists"""
        return os.path.exists(os.path.join(self.missions_dir, mission_name))
