import os
from datetime import datetime
from typing import Dict, Optional
from utils.path_manager import PathManager
from utils.logger import Logger

class ChatLogger:
    def __init__(self, mission_name: str):
        """
        Initialize ChatLogger for a specific mission
        
        Args:
            mission_name: Name of the current mission
        """
        self.logger = Logger()
        self.mission_name = self._normalize_mission_name(mission_name)
        self.chats_dir = self._get_chats_directory()

    def _normalize_mission_name(self, mission_name: str) -> str:
        """
        Normalize mission name for filesystem use
        
        Args:
            mission_name: Original mission name
        
        Returns:
            Normalized mission name
        """
        return mission_name.lower().replace(' ', '_').replace('-', '_')

    def _get_chats_directory(self) -> str:
        """
        Get or create the chats directory for the mission
        
        Returns:
            Path to the chats directory
        """
        chats_dir = os.path.join(PathManager.get_project_root(), "chats", self.mission_name)
        os.makedirs(chats_dir, exist_ok=True)
        return chats_dir

    def log_agent_interaction(
        self, 
        agent_name: str, 
        prompt: str, 
        response: str, 
        files_context: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Log an agent interaction to the chat file
        
        Args:
            agent_name: Name of the agent
            prompt: Prompt sent to the agent
            response: Agent's response
            files_context: Optional context of files involved
        
        Returns:
            bool: Whether logging was successful
        """
        try:
            # Normalize agent name
            normalized_agent_name = agent_name.lower().replace(' ', '_')
            chat_file_path = os.path.join(self.chats_dir, f"{normalized_agent_name}.md")
            
            # Prepare log entry
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"\n## {timestamp}\n\n"
            
            # Add files context if provided
            if files_context:
                log_entry += "### Files Context:\n"
                for filename, content in files_context.items():
                    log_entry += f"#### {filename}\n```\n{content}\n```\n\n"
            
            # Add prompt and response
            log_entry += f"### Prompt:\n{prompt}\n\n"
            log_entry += f"### Response:\n{response}\n"
            
            # Append to chat file
            with open(chat_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            self.logger.log(
                f"Logged interaction for {agent_name} in {chat_file_path}", 
                'success'
            )
            return True
        
        except Exception as e:
            self.logger.log(
                f"Error logging chat for {agent_name}: {str(e)}", 
                'error'
            )
            return False
