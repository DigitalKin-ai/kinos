"""
ParallagonAgent - Base class for autonomous parallel agents
"""
import re
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from search_replace import SearchReplace, SearchReplaceResult


class ParallagonAgent:
    """Base class for Parallagon autonomous agents"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the agent with configuration"""
        self.config = config
        self.file_path = config["file_path"]
        self.check_interval = config.get("check_interval", 5)
        self.running = False

    def _validate_markdown_response(self, response: str) -> bool:
        """Validate that LLM response follows required markdown format"""
        # Exception for ProductionAgent which returns raw text
        if self.__class__.__name__ == "ProductionAgent":
            return True
            
        required_sections = ["État Actuel", "Signaux", "Contenu Principal", "Historique"]
        
        # Check starts with État Actuel
        if not response.startswith("# État Actuel"):
            print(f"[{self.__class__.__name__}] Response must start with '# État Actuel'")
            return False
            
        # Check all required sections present
        for section in required_sections:
            if f"# {section}" not in response:
                print(f"[{self.__class__.__name__}] Missing required section: {section}")
                return False
                
        # Check status format
        if not re.search(r'\[status: \w+\]', response):
            print(f"[{self.__class__.__name__}] Invalid or missing status")
            return False
            
        return True

    def validate_content(self) -> bool:
        """Validate file content structure and format"""
        try:
            # Check basic structure
            if not self.current_content:
                print(f"[{self.__class__.__name__}] Empty content")
                return False
                
            # Check required sections
            required_sections = ["État Actuel", "Signaux", "Contenu Principal", "Historique"]
            for section in required_sections:
                if f"# {section}" not in self.current_content:
                    print(f"[{self.__class__.__name__}] Missing section: {section}")
                    return False
                    
            # Check status format
            status_match = re.search(r'\[status: (\w+)\]', self.current_content)
            if not status_match:
                print(f"[{self.__class__.__name__}] Invalid status format")
                return False
                
            return True
            
        except Exception as e:
            print(f"[{self.__class__.__name__}] Validation error: {str(e)}")
            return False

    def read_files(self) -> None:
        """Read all relevant files for the agent"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.current_content = f.read()
            
            # Read other relevant files based on agent type
            self.other_files = {}
            for file_path in self.config.get("watch_files", []):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.other_files[file_path] = f.read()
        except Exception as e:
            print(f"Error reading files: {e}")
            raise

    def analyze(self) -> None:
        """Analyze changes and signals"""
        try:
            # Extract current status
            status_match = re.search(r'\[status: (\w+)\]', self.current_content)
            self.current_status = status_match.group(1) if status_match else "UNKNOWN"

            # Extract signals section
            signals_match = re.search(r'# Signaux\n(.*?)(?=\n#|$)', 
                                    self.current_content, 
                                    re.DOTALL)
            if signals_match:
                signals_text = signals_match.group(1).strip()
                self.signals = [s.strip() for s in signals_text.split('\n') if s.strip()]
            else:
                self.signals = []

            # Analyze current content and other files to determine needed actions
            self.determine_actions()

        except Exception as e:
            print(f"Error in analysis: {e}")
            raise

    def determine_actions(self) -> None:
        """Determine what actions need to be taken based on current state"""
        # This method should be implemented by specific agent subclasses
        pass

    def _get_llm_response(self, context: dict) -> str:
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    temperature=0,
                    messages=[{"role": "user", "content": self._build_prompt(context)}]
                )
                
                content = response.content[0].text
                if self._validate_markdown_response(content):
                    return content
                print(f"[{self.__class__.__name__}] Invalid response format, retrying...")
                
            except Exception as e:
                print(f"[{self.__class__.__name__}] Attempt {attempt+1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    
        return context[self.__class__.__name__.lower().replace('agent', '')]

    def update(self) -> None:
        """Make necessary updates to files"""
        try:
            if hasattr(self, 'new_content') and self.new_content != self.current_content:
                print(f"[{self.__class__.__name__}] Updating file {self.file_path}")  # Debug log
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(self.new_content)
                self.current_content = self.new_content
                print(f"[{self.__class__.__name__}] File updated successfully")  # Debug log
        except Exception as e:
            print(f"[{self.__class__.__name__}] Error updating file: {str(e)}")  # Error log
            raise

    def update_section(self, section_name: str, new_content: str) -> bool:
        """Update a specific section in the markdown file"""
        try:
            result = SearchReplace.section_replace(self.current_content, section_name, new_content)
            if result.success:
                self.new_content = result.new_content
                return True
            print(f"Error updating section: {result.message}")
            return False
        except Exception as e:
            print(f"Error updating section: {e}")
            return False

    def run(self) -> None:
        """Main agent loop"""
        self.running = True
        while self.running:
            try:
                self.read_files()
                self.analyze()
                self.update()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Error in agent loop: {e}")
                # TODO: Add proper error handling and logging
