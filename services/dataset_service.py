"""
DatasetService - Service for managing fine-tuning dataset creation
"""
import os
import json
import time
import asyncio
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
from utils.path_manager import PathManager
from services.base_service import BaseService
from utils.exceptions import ServiceError
from utils.logger import Logger  # Add Logger import

class DatasetService(BaseService):
    """Manages dataset creation for fine-tuning"""

    def __init__(self, _):  # Keep parameter for compatibility but don't use it
        """Initialize dataset service with explicit configuration"""
        try:
            # Initialize logger first
            self.logger = Logger()
            
            # Get data directory path using PathManager
            self.data_dir = os.path.join(PathManager.get_project_root(), "data")
            os.makedirs(self.data_dir, exist_ok=True)
            
            self.dataset_file = os.path.join(self.data_dir, "fine-tuning.jsonl")
            
            # Create dataset file if it doesn't exist
            if not os.path.exists(self.dataset_file):
                try:
                    with open(self.dataset_file, 'w', encoding='utf-8') as f:
                        pass  # Create empty file
                    self.logger.log(f"Created new dataset file: {self.dataset_file}", 'info')
                except Exception as e:
                    self.logger.log(f"Error creating dataset file: {str(e)}", 'error')
                    raise
            
            # Verify service availability immediately
            if not self.is_available():
                self.logger.log(
                    "Dataset service initialization failed - service may be unreliable", 
                    'warning'
                )
                return
                
            # Log successful initialization with stats
            stats = self.get_dataset_stats()
            self.logger.log(
                f"Dataset service initialized successfully:\n"
                f"- File: {self.dataset_file}\n"
                f"- Entries: {stats['total_entries']}\n"
                f"- Total files: {stats['total_files']}\n"
                f"- Size: {stats['size_bytes']} bytes", 
                'success'
            )
            
            # Start cleanup timer
            self._start_cleanup_timer()
            
            # Verify service availability immediately
            if not self.is_available():
                self.logger.log(
                    "Dataset service initialization failed - service may be unreliable", 
                    'warning'
                )
                return
                
            # Log successful initialization with stats
            stats = self.get_dataset_stats()
            self.logger.log(
                f"Dataset service initialized successfully:\n"
                f"- File: {self.dataset_file}\n"
                f"- Entries: {stats['total_entries']}\n"
                f"- Total files: {stats['total_files']}\n"
                f"- Size: {stats['size_bytes']} bytes", 
                'success'
            )
            
            # Start cleanup timer
            self._start_cleanup_timer()
        except Exception as e:
            self.logger.log(f"Error initializing dataset service: {str(e)}", 'error')
            raise ServiceError(f"Failed to initialize dataset service: {str(e)}")


    def _format_files_context(self, files_context: Dict[str, str]) -> str:
        """Format files context into a readable string with clear file boundaries"""
        formatted = []
        for filename, content in files_context.items():
            formatted.append(f"File: {filename}\n```\n{content}\n```\n")
        return "\n".join(formatted)

    async def add_interaction_async(self, prompt: str, files_context: Dict[str, str], 
                                  aider_response: str, weight: float = 0) -> None:
        """Asynchronously add an interaction to the dataset"""
        try:
            self.logger.log(
                f"💾 Starting dataset interaction processing:\n"
                f"Prompt length: {len(prompt)}\n"
                f"Number of files: {len(files_context)}\n"
                f"Response length: {len(aider_response)}\n"
                f"Dataset file: {self.dataset_file}",
                'debug'
            )
            
            # Validate inputs
            if not prompt or not files_context or not aider_response:
                raise ValueError("Missing required interaction data")

            # Format files context
            formatted_context = self._format_files_context(files_context)
            
            # Format user message with context
            user_message = f"Context:\n{formatted_context}\n\nTask:\n{prompt}"
            
            # Create dataset entry
            entry = {
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": aider_response}
                ],
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "num_files": len(files_context),
                    "files": list(files_context.keys())
                }
            }
            
            # Append to file with explicit error handling
            try:
                with open(self.dataset_file, 'a', encoding='utf-8') as f:
                    json_str = json.dumps(entry, ensure_ascii=False)
                    f.write(json_str + '\n')
                    f.flush()  # Force write to disk
                    os.fsync(f.fileno())  # Ensure it's written to disk
                    
                self.logger.log(
                    f"Added interaction to dataset (files: {len(files_context)})", 
                    'success'
                )
                
            except IOError as e:
                self.logger.log(f"IO Error writing to dataset: {str(e)}", 'error')
                raise ServiceError(f"Failed to write to dataset: {str(e)}")
                
        except Exception as e:
            self.logger.log(
                f"Error adding interaction to dataset:\n"
                f"Error: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}", 
                'error'
            )

    def _format_files_context(self, files_context: Dict[str, str]) -> str:
        """Format files context into a readable string with clear file boundaries"""
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
            
    def _calculate_weight(self, original_content: Dict[str, str], aider_response: str) -> Optional[float]:
        """Calculate interaction weight with detailed logging"""
        try:
            self.logger.log("Calculating interaction weight", 'debug')
            
            # Check for required keywords
            if not ("SEARCH" in aider_response and "REPLACE" in aider_response):
                self.logger.log("Response missing required keywords - skipping entry", 'debug')
                return None
                
            # Base weight
            weight = 0.5
            
            # Increase weight for longer responses
            if len(aider_response) > 1000:
                weight += 0.1
                self.logger.log("Weight increased for long response", 'debug')
                
            # Increase weight for multi-file changes
            if len(original_content) > 1:
                file_bonus = 0.1 * len(original_content)
                weight += file_bonus
                self.logger.log(f"Weight increased by {file_bonus:.2f} for multiple files", 'debug')
                
            # Cap weight at 1.0
            final_weight = min(1.0, weight)
            self.logger.log(f"Final calculated weight: {final_weight:.2f}", 'debug')
            return final_weight
            
        except Exception as e:
            self.logger.log(f"Error calculating weight: {str(e)}", 'error')
            return None

    def _start_cleanup_timer(self):
        """Start periodic dataset cleanup with enhanced logging"""
        import threading
        
        def cleanup_task():
            while True:
                try:
                    time.sleep(3600)  # Sleep for 1 hour
                    self.logger.log("Starting dataset cleanup", 'info')
                    
                    # Remove duplicate entries
                    unique_entries = set()
                    cleaned_entries = []
                    duplicates = 0
                    
                    with open(self.dataset_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            entry_hash = hash(line.strip())
                            if entry_hash not in unique_entries:
                                unique_entries.add(entry_hash)
                                cleaned_entries.append(line)
                            else:
                                duplicates += 1
                    
                    # Write back cleaned entries
                    with open(self.dataset_file, 'w', encoding='utf-8') as f:
                        f.writelines(cleaned_entries)
                        
                    self.logger.log(
                        f"Dataset cleanup completed:\n"
                        f"- Removed duplicates: {duplicates}\n"
                        f"- Remaining entries: {len(cleaned_entries)}", 
                        'success'
                    )
                    
                except Exception as e:
                    self.logger.log(
                        f"Error in dataset cleanup:\n"
                        f"Error: {str(e)}\n"
                        f"Traceback: {traceback.format_exc()}", 
                        'error'
                    )
        
        thread = threading.Thread(target=cleanup_task, daemon=True)
        thread.start()
        self.logger.log("Dataset cleanup timer started", 'info')

    def _validate_dataset_file(self) -> bool:
        """Validate dataset file structure and permissions"""
        try:
            # Check if file exists
            if not os.path.exists(self.dataset_file):
                self.logger.log("Dataset file does not exist - will be created", 'info')
                return True
                
            # Check permissions
            if not os.access(os.path.dirname(self.dataset_file), os.W_OK):
                raise ServiceError("No write permission on dataset directory")
                
            # Validate file format
            with open(self.dataset_file, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    try:
                        entry = json.loads(line)
                        if not self._validate_entry_format(entry):
                            self.logger.log(f"Invalid entry format at line {i}", 'warning')
                    except json.JSONDecodeError:
                        self.logger.log(f"Invalid JSON at line {i}", 'warning')
                        
            return True
            
        except Exception as e:
            self.logger.log(f"Dataset file validation failed: {str(e)}", 'error')
            return False

    def _validate_entry_format(self, entry: Dict) -> bool:
        """Validate format of a dataset entry"""
        try:
            # Check required fields and types
            if 'messages' not in entry:
                return False
            
            if not isinstance(entry['messages'], list):
                return False
            
            # Validate messages format
            for msg in entry['messages']:
                if not all(k in msg for k in ('role', 'content')):
                    return False
                if not isinstance(msg.get('role'), str) or not isinstance(msg.get('content'), str):
                    return False
                    
            return True
            
        except Exception:
            return False

    def get_dataset_stats(self) -> Dict[str, Any]:
        """Get statistics about the dataset"""
        try:
            stats = {
                'total_entries': 0,
                'total_files': 0,
                'avg_weight': 0.0,
                'file_types': {},
                'entry_dates': [],
                'size_bytes': 0
            }
            
            if not os.path.exists(self.dataset_file):
                return stats
                
            weights_sum = 0
            
            with open(self.dataset_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        stats['total_entries'] += 1
                        stats['total_files'] += entry['metadata']['num_files']
                        weights_sum += entry['metadata']['weight']
                        stats['entry_dates'].append(entry['metadata']['timestamp'])
                    except:
                        continue
                        
            if stats['total_entries'] > 0:
                stats['avg_weight'] = weights_sum / stats['total_entries']
                
            stats['size_bytes'] = os.path.getsize(self.dataset_file)
            
            return stats
            
        except Exception as e:
            self.logger.log(f"Error getting dataset stats: {str(e)}", 'error')
            return {}

    def is_available(self) -> bool:
        """Check if dataset service is properly initialized and available"""
        try:
            # Verify essential attributes
            if not hasattr(self, 'data_dir') or not hasattr(self, 'dataset_file'):
                self.logger.log("Missing essential attributes in dataset service", 'error')
                return False

            # Verify data directory exists and is writable
            if not os.path.exists(self.data_dir):
                try:
                    os.makedirs(self.data_dir, exist_ok=True)
                    self.logger.log(f"Created data directory: {self.data_dir}", 'info')
                except Exception as e:
                    self.logger.log(f"Cannot create data directory: {str(e)}", 'error')
                    return False

            if not os.access(self.data_dir, os.W_OK):
                self.logger.log(f"Data directory not writable: {self.data_dir}", 'error')
                return False

            # Verify dataset file exists and is writable
            if not os.path.exists(self.dataset_file):
                try:
                    # Try to create and write to the file
                    with open(self.dataset_file, 'a', encoding='utf-8') as f:
                        f.write("")  # Write empty string to verify write access
                    self.logger.log(f"Created dataset file: {self.dataset_file}", 'info')
                except Exception as e:
                    self.logger.log(f"Cannot create dataset file: {str(e)}", 'error')
                    return False
            else:
                if not os.access(self.dataset_file, os.W_OK):
                    self.logger.log(f"Dataset file not writable: {self.dataset_file}", 'error')
                    return False

            # Try to read the file to verify full access
            try:
                with open(self.dataset_file, 'r', encoding='utf-8') as f:
                    pass
            except Exception as e:
                self.logger.log(f"Cannot read dataset file: {str(e)}", 'error')
                return False

            self.logger.log("Dataset service is available and fully functional", 'success')
            return True

        except Exception as e:
            self.logger.log(f"Error checking dataset service availability: {str(e)}", 'error')
            return False

    def diagnose(self) -> Dict[str, Any]:
        """Run diagnostics and return detailed status"""
        try:
            status = {
                'initialized': hasattr(self, 'data_dir') and hasattr(self, 'dataset_file'),
                'data_dir': {
                    'path': getattr(self, 'data_dir', None),
                    'exists': False,
                    'writable': False
                },
                'dataset_file': {
                    'path': getattr(self, 'dataset_file', None),
                    'exists': False,
                    'writable': False,
                    'readable': False
                },
                'stats': None,
                'errors': []
            }

            # Check data directory
            if status['data_dir']['path']:
                status['data_dir']['exists'] = os.path.exists(self.data_dir)
                if status['data_dir']['exists']:
                    status['data_dir']['writable'] = os.access(self.data_dir, os.W_OK)

            # Check dataset file
            if status['dataset_file']['path']:
                status['dataset_file']['exists'] = os.path.exists(self.dataset_file)
                if status['dataset_file']['exists']:
                    status['dataset_file']['writable'] = os.access(self.dataset_file, os.W_OK)
                    status['dataset_file']['readable'] = os.access(self.dataset_file, os.R_OK)

            # Get stats if possible
            if self.is_available():
                try:
                    status['stats'] = self.get_dataset_stats()
                except Exception as e:
                    status['errors'].append(f"Error getting stats: {str(e)}")

            return status

        except Exception as e:
            self.logger.log(f"Error running diagnostics: {str(e)}", 'error')
            return {
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    def cleanup(self):
        """Cleanup dataset service resources with logging"""
        try:
            self.logger.log("Starting dataset service cleanup", 'info')
            
            # Ensure all pending writes are completed
            with open(self.dataset_file, 'a', encoding='utf-8') as f:
                f.flush()
                os.fsync(f.fileno())
                
            # Clear caches
            self.content_cache.clear()
            
            self.logger.log("Dataset service cleanup completed", 'success')
            
        except Exception as e:
            self.logger.log(
                f"Error during dataset service cleanup:\n"
                f"Error: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}", 
                'error'
            )
