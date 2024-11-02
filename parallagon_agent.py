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

    def update(self) -> None:
        """Make necessary updates to files"""
        try:
            if hasattr(self, 'new_content') and self.new_content != self.current_content:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(self.new_content)
                self.current_content = self.new_content
        except Exception as e:
            print(f"Error updating files: {e}")
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
