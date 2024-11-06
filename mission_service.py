import os
from datetime import datetime
from typing import List, Dict, Optional

class MissionService:
    def __init__(self):
        self.missions_dir = "missions"
        os.makedirs(self.missions_dir, exist_ok=True)
        
    def _resolve_mission_path(self, mission_path: str) -> str:
        """Resolve real path if it's a symlink"""
        try:
            if os.path.islink(mission_path):
                return os.path.realpath(mission_path)
            return mission_path
        except Exception as e:
            print(f"Error resolving path: {e}")
            return mission_path

    def _is_valid_mission_dir(self, mission_dir: str) -> bool:
        """Ensure directory contains all required mission files by creating them if missing"""
        required_files = [
            "demande.md",
            "specifications.md", 
            "management.md",
            "production.md",
            "evaluation.md",
            "suivi.md",
            "contexte.md"
        ]
        
        try:
            # Create any missing required files
            for file_name in required_files:
                file_path = os.path.join(mission_dir, file_name)
                if not os.path.isfile(file_path):
                    print(f"Creating missing file: {file_path}")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"# {file_name[:-3].capitalize()}\n[Initial content]")
            
            return True
            
        except Exception as e:
            print(f"Error creating mission files: {e}")
            return False

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
        """Get all missions by reading directories and symlinks"""
        try:
            missions = []
            if os.path.exists(self.missions_dir):
                print(f"\nScanning missions directory: {self.missions_dir}")  # Debug
                for mission_name in os.listdir(self.missions_dir):
                    mission_path = os.path.join(self.missions_dir, mission_name)
                    real_path = self._resolve_mission_path(mission_path)
                    
                    # Debug logs détaillés
                    print(f"\nMission trouvée: {mission_name}")
                    print(f"Chemin: {mission_path}")
                    print(f"Chemin réel: {real_path}")
                    print(f"Est un symlink: {os.path.islink(mission_path)}")
                    print(f"Est un dossier: {os.path.isdir(real_path)}")
                    if os.path.isdir(real_path):
                        print("Contenu du dossier:")
                        try:
                            print(os.listdir(real_path))
                        except Exception as e:
                            print(f"Erreur lecture dossier: {e}")
                    
                    if (os.path.isdir(real_path) and 
                        self._is_valid_mission_dir(real_path)):
                        mission = {
                            'id': len(missions) + 1,
                            'name': mission_name,
                            'description': '',
                            'status': 'active',
                            'created_at': datetime.fromtimestamp(os.path.getctime(real_path)).isoformat(),
                            'updated_at': datetime.fromtimestamp(os.path.getmtime(real_path)).isoformat(),
                            'external_path': real_path if os.path.islink(mission_path) else None
                        }
                        missions.append(mission)
                        print(f"Mission ajoutée: {mission}")
                    else:
                        print(f"Mission ignorée: n'est pas un dossier valide")

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

    def create_mission_link(self, external_path: str, mission_name: str = None) -> Dict:
        """Create a symbolic link to an external mission folder"""
        try:
            # Validate external path exists and is a directory
            if not os.path.isdir(external_path):
                raise ValueError(f"Path does not exist or is not a directory: {external_path}")
                
            # Use provided name or extract from path
            if not mission_name:
                mission_name = os.path.basename(external_path.rstrip('/\\'))
                
            # Create link path in missions directory
            link_path = os.path.join(self.missions_dir, mission_name)
            
            # Check if mission already exists
            if os.path.exists(link_path):
                raise ValueError(f"Mission '{mission_name}' already exists")

            # Define required files
            required_files = [
                "demande.md",
                "specifications.md", 
                "management.md",
                "production.md",
                "evaluation.md",
                "suivi.md"
            ]

            # Create any missing required files in the external directory first
            for file_name in required_files:
                file_path = os.path.join(external_path, file_name)
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"# {file_name[:-3].capitalize()}\n[Initial content]")
                
            # Sur Windows, au lieu d'un symlink, créer une copie des fichiers
            if os.name == 'nt':  # Windows
                os.makedirs(link_path)
                
                # Copier les fichiers
                for file_name in required_files:
                    src_file = os.path.join(external_path, file_name)
                    dst_file = os.path.join(link_path, file_name)
                    import shutil
                    shutil.copy2(src_file, dst_file)
            else:
                # Sur les autres systèmes, utiliser un symlink
                os.symlink(external_path, link_path, target_is_directory=True)
            
            # Return mission info
            return {
                'id': len(self.get_all_missions()),
                'name': mission_name,
                'description': f"External mission at {external_path}",
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'external_path': external_path
            }
            
        except Exception as e:
            print(f"Error creating mission link: {e}")
            raise

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
