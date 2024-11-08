import os
from datetime import datetime
from typing import List, Dict, Optional
from file_manager import FileManager

class MissionService:
    def __init__(self):
        self.missions_dir = "missions"
        os.makedirs(self.missions_dir, exist_ok=True)
        
    def _resolve_mission_path(self, mission_path: str) -> str:
        """Resolve real path if it's a symlink"""
        try:
            # Convert to absolute path
            abs_path = os.path.abspath(mission_path)
            
            # Resolve symlink if present
            if os.path.islink(abs_path):
                real_path = os.path.realpath(abs_path)
                # Verify the real path exists
                if not os.path.exists(real_path):
                    raise ValueError(f"Broken symlink: {mission_path} -> {real_path}")
                return real_path
                
            return abs_path
            
        except Exception as e:
            print(f"Error resolving path: {e}")
            return mission_path

    REQUIRED_FILES = [
        "demande.md",
        "specifications.md", 
        "management.md",
        "production.md",
        "evaluation.md",
        "suivi.md"
    ]

    def create_mission(self, name: str, description: str = None) -> Dict:
        """Create a new mission directory"""
        try:
            mission_dir = os.path.join(self.missions_dir, name)
            if os.path.exists(mission_dir):
                raise ValueError(f"Mission '{name}' already exists")
                
            os.makedirs(mission_dir)
            
            # Utiliser FileManager pour créer les fichiers
            file_manager = FileManager({}, None)  # Pas besoin de paths ou callback ici
            if not file_manager.create_mission_files(name):
                # Cleanup on failure
                import shutil
                shutil.rmtree(mission_dir, ignore_errors=True)
                raise Exception("Failed to create mission files")
                
            return {
                'id': len(self.get_all_missions()),
                'name': name,
                'description': description,
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        except Exception as e:
            raise Exception(f"Failed to create mission: {str(e)}")

    def get_all_missions(self) -> List[Dict]:
        """Get all missions by reading directories and symlinks"""
        try:
            missions = []
            if not os.path.exists(self.missions_dir):
                os.makedirs(self.missions_dir)
                return missions

            print(f"Scanning missions directory: {os.path.abspath(self.missions_dir)}")
            
            for mission_name in os.listdir(self.missions_dir):
                try:
                    mission_path = os.path.join(self.missions_dir, mission_name)
                    real_path = self._resolve_mission_path(mission_path)
                    
                    print(f"\nAnalyzing mission: {mission_name}")
                    print(f"Path: {mission_path}")
                    print(f"Real path: {real_path}")
                    
                    if os.path.isdir(real_path):
                        has_required_files = any(
                            os.path.exists(os.path.join(real_path, req_file))
                            for req_file in self.REQUIRED_FILES
                        )
                        
                        if has_required_files:
                            mission = {
                                'id': len(missions) + 1,
                                'name': mission_name,
                                'description': '',
                                'status': 'active',
                                'created_at': datetime.fromtimestamp(
                                    os.path.getctime(real_path)
                                ).isoformat(),
                                'updated_at': datetime.fromtimestamp(
                                    os.path.getmtime(real_path)
                                ).isoformat(),
                                'external_path': real_path if os.path.islink(mission_path) else None
                            }
                            missions.append(mission)
                            print(f"✓ Added mission: {mission_name}")
                        else:
                            print(f"⚠️ Skipped mission {mission_name}: missing required files")
                    else:
                        print(f"⚠️ Skipped {mission_name}: not a valid directory")

                except Exception as e:
                    print(f"Error processing mission {mission_name}: {str(e)}")
                    continue

            print(f"\nTotal missions found: {len(missions)}")
            return missions
            
        except Exception as e:
            print(f"❌ Error scanning missions: {str(e)}")
            import traceback
            print(traceback.format_exc())
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
    def is_valid_mission(self, mission_path: str) -> bool:
        """Vérifie si un dossier de mission est valide"""
        try:
            # Vérifier si c'est un dossier
            if not os.path.isdir(mission_path):
                return False
                
            # Vérifier la présence d'au moins un fichier requis
            return any(
                os.path.exists(os.path.join(mission_path, req_file))
                for req_file in self.REQUIRED_FILES
            )
        except Exception as e:
            print(f"Error validating mission {mission_path}: {str(e)}")
            return False
