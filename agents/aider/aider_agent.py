"""
AiderAgent - Core implementation of Aider-based agent functionality
"""
import os
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from utils.logger import Logger
from utils.exceptions import AgentError
from agents.base.agent_base import AgentBase
from agents.aider.command_builder import AiderCommandBuilder
from agents.aider.output_parser import AiderOutputParser
from agents.utils.encoding import configure_encoding
from agents.utils.path_utils import validate_paths, get_relative_path
from agents.utils.rate_limiter import RateLimiter

class AiderAgent(AgentBase):
    """
    Agent implementation using Aider for file modifications.
    Handles:
    - Command construction and execution
    - Output parsing and processing
    - Rate limiting and retries
    - Path management and validation
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize agent with configuration"""
        super().__init__(config)
        
        # Configure UTF-8 encoding
        configure_encoding()
        
        # Initialize components
        self.command_builder = AiderCommandBuilder()
        self.output_parser = AiderOutputParser(self.logger)
        self.rate_limiter = RateLimiter(
            max_requests=50,
            time_window=60
        )
        
        # Store original directory
        self.original_dir = os.getcwd()
        
        # Initialize state
        self._init_state()
        
        # Validate paths
        if not validate_paths(self.mission_dir):
            raise ValueError(f"Invalid mission directory: {self.mission_dir}")

    def _run_aider(self, prompt: str) -> Optional[str]:
        """Execute Aider with given prompt"""
        try:
            # Rate limiting check
            if not self.rate_limiter.should_allow_request():
                wait_time = self.rate_limiter.get_wait_time()
                self.logger.log(f"Rate limit reached. Waiting {wait_time:.1f}s", 'warning')
                return None
            
            # Change to mission directory
            os.chdir(self.mission_dir)
            
            try:
                # Build command
                cmd = self.command_builder.build_command(
                    prompt=prompt,
                    files=list(self.mission_files.keys())
                )
                
                # Execute command
                process = self.command_builder.execute_command(cmd)
                
                # Parse output
                result = self.output_parser.parse_output(process)
                
                # Update metrics
                self.rate_limiter.record_request()
                
                return result
                
            finally:
                # Restore original directory
                os.chdir(self.original_dir)
                
        except Exception as e:
            self.logger.log(f"Error running Aider: {str(e)}", 'error')
            return None

    def list_files(self) -> None:
        """List all text files in mission directory"""
        try:
            if not os.path.exists(self.mission_dir):
                self.logger.log("Mission directory not found", 'error')
                self.mission_files = {}
                return

            # Get ignore patterns
            ignore_patterns = self.command_builder.get_ignore_patterns(
                self.mission_dir
            )
            
            # List files
            text_files = {}
            for root, _, files in os.walk(self.mission_dir):
                for file in files:
                    if file.endswith(('.md', '.txt', '.py', '.js')):
                        file_path = os.path.join(root, file)
                        rel_path = get_relative_path(file_path, self.mission_dir)
                        
                        # Skip ignored files
                        if any(pattern in rel_path for pattern in ignore_patterns):
                            continue
                            
                        text_files[file_path] = os.path.getmtime(file_path)
            
            self.mission_files = text_files
            
        except Exception as e:
            self.logger.log(f"Error listing files: {str(e)}", 'error')
            self.mission_files = {}

    def cleanup(self):
        """Cleanup agent resources"""
        try:
            # Stop agent if running
            if self.running:
                self.stop()
            
            # Restore original directory
            if hasattr(self, 'original_dir'):
                try:
                    os.chdir(self.original_dir)
                except Exception as e:
                    self.logger.log(f"Error restoring directory: {str(e)}", 'error')
            
            # Clear caches
            self._prompt_cache.clear()
            self.mission_files.clear()
            
            # Base cleanup
            super().cleanup()
            
        except Exception as e:
            self.logger.log(f"Error in cleanup: {str(e)}", 'error')
