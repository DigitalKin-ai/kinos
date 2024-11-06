import os
from datetime import datetime
from typing import List, Dict, Optional
from database import Database

class MissionService:
    def __init__(self):
        self.db = Database()

    def create_mission(self, name: str, description: str = None) -> Dict:
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO missions (name, description)
                VALUES (%s, %s)
                RETURNING id, name, description, status, 
                         created_at, updated_at
                """,
                (name, description)
            )
            return cursor.fetchone()

    def get_all_missions(self) -> List[Dict]:
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, description, status, 
                       created_at, updated_at
                FROM missions
                ORDER BY created_at DESC
                """
            )
            return cursor.fetchall()

    def get_mission(self, mission_id: int) -> Optional[Dict]:
        """Get a mission by ID with file paths"""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, description, status, 
                       created_at, updated_at
                FROM missions
                WHERE id = %s
                """,
                (mission_id,)
            )
            mission = cursor.fetchone()
            if mission:
                # Add file paths
                mission_dir = os.path.join("missions", mission['name'])
                mission['files'] = {
                    'demande': os.path.join(mission_dir, "demande.md"),
                    'specifications': os.path.join(mission_dir, "specifications.md"),
                    'management': os.path.join(mission_dir, "management.md"),
                    'production': os.path.join(mission_dir, "production.md"),
                    'evaluation': os.path.join(mission_dir, "evaluation.md"),
                    'suivi': os.path.join(mission_dir, "suivi.md")
                }
            return mission

    def update_mission(self, mission_id: int, name: str = None, 
                      description: str = None, status: str = None) -> Optional[Dict]:
        updates = []
        values = []
        if name is not None:
            updates.append("name = %s")
            values.append(name)
        if description is not None:
            updates.append("description = %s")
            values.append(description)
        if status is not None:
            updates.append("status = %s")
            values.append(status)
            
        if not updates:
            return None
            
        values.append(mission_id)
        
        with self.db.get_cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE missions 
                SET {", ".join(updates)}
                WHERE id = %s
                RETURNING id, name, description, status, 
                          created_at, updated_at
                """,
                tuple(values)
            )
            return cursor.fetchone()

    def save_mission_file(self, mission_id: int, file_type: str, content: str) -> bool:
        """Save content to a mission file"""
        try:
            mission = self.get_mission(mission_id)
            if not mission or file_type not in mission['files']:
                return False
                
            file_path = mission['files'][file_type]
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return True
            
        except Exception as e:
            print(f"Error saving mission file: {e}")
            return False

    def delete_mission(self, mission_id: int) -> bool:
        """Delete a mission from the database"""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM missions 
                WHERE id = %s
                RETURNING id
                """,
                (mission_id,)
            )
            return cursor.fetchone() is not None
