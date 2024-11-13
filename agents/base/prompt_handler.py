"""Prompt management and caching"""
import os
from typing import Optional, Dict, Any
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
