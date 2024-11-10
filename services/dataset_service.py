"""
DatasetService - Service for managing fine-tuning dataset creation
"""
import os
import json
import time
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from utils.path_manager import PathManager
from services.base_service import BaseService

class DatasetService(BaseService):
    """Manages dataset creation for fine-tuning"""

    def __init__(self, web_instance):
        super().__init__(web_instance)
        self.dataset_file = os.path.join(PathManager.get_project_root(), "data", "fine-tuning.jsonl")
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.dataset_file), exist_ok=True)
        # Start cleanup timer
        self._start_cleanup_timer()

    async def add_interaction_async(self, prompt: str, files_context: Dict[str, str], 
                                  aider_response: str, weight: float = 0) -> None:
        """
        Asynchronously add an interaction to the dataset
        
        Args:
            prompt: The original prompt used
            files_context: Dict of filename -> content for context
            aider_response: Raw response from Aider
            weight: Importance weight for this example (0-1)
        """
        try:
            # Format files context
            formatted_context = self._format_files_context(files_context)
            
            # Format user message with context
            user_message = f"Context:\n{formatted_context}\n\nTask:\n{prompt}"
            
            # Parse Aider response
            parsed_response = self._parse_aider_response(aider_response)
            
            # Create dataset entry
            entry = {
                "messages": [
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": user_message
                    },
                    {
                        "role": "assistant",
                        "content": parsed_response,
                        "weight": weight
                    }
                ]
            }
            
            # Append to file without loading entire file
            with open(self.dataset_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                
            self.logger.log(f"Added new interaction to dataset", 'success')
            
        except Exception as e:
            self.logger.log(f"Error adding interaction to dataset: {str(e)}", 'error')

    def _format_files_context(self, files_context: Dict[str, str]) -> str:
        """Format files context into a readable string"""
        formatted = []
        for filename, content in files_context.items():
            formatted.append(f"File: {filename}\n```\n{content}\n```\n")
        return "\n".join(formatted)

    def _parse_aider_response(self, response: str) -> str:
        """
        Parse Aider's response to extract relevant content
        Removes command output and keeps only the actual changes/responses
        """
        try:
            # Split on common Aider output markers
            lines = response.split('\n')
            parsed_lines = []
            in_relevant_section = False
            
            for line in lines:
                # Skip Aider command output and status messages
                if any(marker in line.lower() for marker in ['running aider', 'executing', '$ git']):
                    continue
                    
                # Include relevant content
                if line.strip() and not line.startswith(('>', '#')):
                    parsed_lines.append(line)
                    
            return '\n'.join(parsed_lines).strip()
            
        except Exception as e:
            self.logger.log(f"Error parsing Aider response: {str(e)}", 'error')
            return response  # Return original response if parsing fails
            
    def _calculate_weight(self, original_content: Dict[str, str], aider_response: str) -> float:
        """Calculate interaction weight based on changes made"""
        try:
            # Base weight
            weight = 0.5
            
            # Increase weight for longer responses
            if len(aider_response) > 1000:
                weight += 0.1
                
            # Increase weight for multi-file changes
            if len(original_content) > 1:
                weight += 0.1 * len(original_content)
                
            # Cap weight at 1.0
            return min(1.0, weight)
            
        except Exception as e:
            self.logger.log(f"Error calculating weight: {str(e)}", 'error')
            return 0.5  # Default weight on error

    def _start_cleanup_timer(self):
        """Start periodic dataset cleanup"""
        import threading
        
        def cleanup_task():
            while True:
                try:
                    # Sleep for 1 hour
                    time.sleep(3600)
                    
                    # Remove duplicate entries
                    unique_entries = set()
                    cleaned_entries = []
                    
                    with open(self.dataset_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            entry_hash = hash(line.strip())
                            if entry_hash not in unique_entries:
                                unique_entries.add(entry_hash)
                                cleaned_entries.append(line)
                    
                    # Write back cleaned entries
                    with open(self.dataset_file, 'w', encoding='utf-8') as f:
                        f.writelines(cleaned_entries)
                        
                    self.logger.log("Dataset cleanup completed", 'info')
                    
                except Exception as e:
                    self.logger.log(f"Error in dataset cleanup: {str(e)}", 'error')
        
        thread = threading.Thread(target=cleanup_task, daemon=True)
        thread.start()

    def cleanup(self):
        """Cleanup any resources used by the dataset service"""
        try:
            # Ensure all pending writes are completed
            with open(self.dataset_file, 'a', encoding='utf-8') as f:
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            self.logger.log(f"Error during dataset service cleanup: {str(e)}", 'error')
