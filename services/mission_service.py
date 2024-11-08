import os
from utils.decorators import safe_operation

class MissionService:
    def __init__(self, web_instance):
        self.web_instance = web_instance
        
    def get_all_missions(self):
        """Get all missions"""
        try:
            return self.web_instance.mission_service.get_all_missions()
        except Exception as e:
            self.web_instance.log_message(f"Error getting missions: {str(e)}", level='error')
            return []
            
    def create_mission(self, name, description=None):
        """Create a new mission"""
        try:
            return self.web_instance.mission_service.create_mission(name, description)
        except Exception as e:
            self.web_instance.log_message(f"Error creating mission: {str(e)}", level='error')
            raise

    @safe_operation()
    def _load_test_data(self) -> str:
        """Load test data from template file"""
        try:
            test_data_path = os.path.join("templates", "test_data", "demande_test_1.md")
            if not os.path.exists(test_data_path):
                self.web_instance.log_message(f"Test data file not found: {test_data_path}", level='error')
                return ""
                
            with open(test_data_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.web_instance.log_message(f"Error loading test data: {str(e)}", level='error')
            return ""
