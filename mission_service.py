import os
from datetime import datetime
from typing import List, Dict, Optional
from database import Database

class MissionService:
    def init_database(self):
        """Initialize database tables if they don't exist"""
        with self.db.get_cursor() as cursor:
            # Create missions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS missions (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Create or replace the update trigger
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
                
                -- Drop trigger if exists
                DROP TRIGGER IF EXISTS update_missions_updated_at ON missions;
                
                -- Create trigger
                CREATE TRIGGER update_missions_updated_at
                    BEFORE UPDATE ON missions
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
            """)

    def __init__(self):
        self.db = Database()
        self.init_database()  # Initialize database on service creation

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
        """Get all missions with error handling"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, name, description, status, 
                           created_at, updated_at
                    FROM missions
                    ORDER BY created_at DESC
                    """
                )
                missions = cursor.fetchall()
                
                # Convert datetime objects to strings for JSON serialization
                for mission in missions:
                    if mission['created_at']:
                        mission['created_at'] = mission['created_at'].isoformat()
                    if mission['updated_at']:
                        mission['updated_at'] = mission['updated_at'].isoformat()
                        
                return missions
                
        except Exception as e:
            print(f"Error getting missions: {e}")
            return []

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

    def mission_exists(self, mission_name: str) -> bool:
        """Check if a mission with the given name already exists"""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM missions
                WHERE name = %s
                """,
                (mission_name,)
            )
            result = cursor.fetchone()
            return result['count'] > 0

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
