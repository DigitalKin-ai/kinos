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
