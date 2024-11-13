"""Prompt management and caching"""
import os
from typing import Optional, Dict, Any
from datetime import datetime
from utils.logger import Logger

class PromptHandler:
    """Manages prompt loading and caching"""
    def __init__(self, logger: Logger):
        self.logger = logger
        self._prompt_cache = {}

    def get_prompt(self, prompt_file: str) -> Optional[str]:
        """Get prompt with caching"""
        try:
            if not prompt_file or not os.path.exists(prompt_file):
                return None

            # Check cache first
            mtime = os.path.getmtime(prompt_file)
            if prompt_file in self._prompt_cache:
                cached_time, cached_content = self._prompt_cache[prompt_file]
                if cached_time == mtime:
                    return cached_content

            # Load and cache prompt
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self._prompt_cache[prompt_file] = (mtime, content)
            return content

        except Exception as e:
            self.logger.log(f"Error getting prompt: {str(e)}", 'error')
            return None

    def save_prompt(self, prompt_file: str, content: str) -> bool:
        """Save prompt with validation"""
        try:
            if not content or not content.strip():
                raise ValueError("Prompt content cannot be empty")

            # Create directory if needed
            os.makedirs(os.path.dirname(prompt_file), exist_ok=True)

            # Write to temp file first
            temp_file = f"{prompt_file}.tmp"
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())

                # Atomic rename
                os.replace(temp_file, prompt_file)

                # Clear cache entry
                if prompt_file in self._prompt_cache:
                    del self._prompt_cache[prompt_file]

                return True

            finally:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass

        except Exception as e:
            self.logger.log(f"Error saving prompt: {str(e)}", 'error')
            return False

    def validate_prompt(self, content: str) -> bool:
        """Validate prompt content format"""
        try:
            if not content or not content.strip():
                return False
                
            # Check minimum size
            if len(content) < 10:
                return False
                
            # Check required sections
            required = ["MISSION:", "CONTEXT:", "INSTRUCTIONS:", "RULES:"]
            for section in required:
                if section not in content:
                    self.logger.log(f"Missing required section: {section}", 'warning')
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.log(f"Error validating prompt: {str(e)}", 'error')
            return False

    def create_backup(self, prompt_file: str) -> bool:
        """Create backup of current prompt"""
        try:
            if not os.path.exists(prompt_file):
                return True
                
            # Create backups directory
            backup_dir = os.path.join(os.path.dirname(prompt_file), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"{os.path.basename(prompt_file)}_{timestamp}")
            
            # Copy current prompt
            import shutil
            shutil.copy2(prompt_file, backup_file)
            
            self.logger.log(f"Created backup: {backup_file}", 'info')
            return True
            
        except Exception as e:
            self.logger.log(f"Error creating backup: {str(e)}", 'error')
            return False
