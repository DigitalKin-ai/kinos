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
            return cursor.fetchone()

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
