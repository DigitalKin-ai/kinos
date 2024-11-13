"""
AiderAgent - Core implementation of Aider-based agent functionality
"""
import os
import time
import subprocess
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from agents.base.agent_base import AgentBase
from agents.base.file_handler import FileHandler
from agents.aider.command_builder import AiderCommandBuilder
from agents.aider.output_parser import AiderOutputParser
from agents.utils.encoding import configure_encoding, detect_file_encoding, normalize_encoding
from agents.utils.rate_limiter import RateLimiter
from utils.commit_logger import CommitLogger
from agents.base.file_handler import FileHandler
from agents.base.prompt_handler import PromptHandler
from utils.path_manager import PathManager
from utils.error_handler import ErrorHandler
from utils.managers.timeout_manager import TimeoutManager
from utils.constants import (
    DEFAULT_TIMEOUT,
    OUTPUT_COLLECTION_TIMEOUT,
    COMMAND_EXECUTION_TIMEOUT
)
from utils.constants import COMMIT_ICONS

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
        
        try:
            # Configure UTF-8 encoding first
            self._configure_encoding()
            
            # Initialize components
            self.command_builder = AiderCommandBuilder()
            self.output_parser = AiderOutputParser(self.logger)
            self.rate_limiter = RateLimiter(max_requests=50, time_window=60)
            self.file_handler = FileHandler(self.mission_dir, self.logger)
            self.prompt_handler = PromptHandler(self.logger)
        
            # Store original directory
            self.original_dir = os.getcwd()
        
            # Resolve prompt file path
            if not self.prompt_file:
                # Try to find default prompt file based on agent name
                from utils.path_manager import PathManager
                default_prompt = f"{self.name.lower()}.md"
                prompts_dir = PathManager.get_prompts_path()
                self.prompt_file = os.path.join(prompts_dir, default_prompt)
                self.logger.log(f"Using default prompt file: {self.prompt_file}", 'info')
        
            # Initialize state tracking
            self._init_state()
            
            self.logger.log(f"[{self.name}] Initialized successfully")
            
        except Exception as e:
            self.logger.log(f"Error during initialization: {str(e)}", 'error')
            raise
        
    def _configure_encoding(self):
        """Configure UTF-8 encoding for the agent"""
        configure_encoding()
        
    def _init_state(self):
        """Initialize agent state tracking"""
        self.running = False
        self.last_run = None
        self.last_change = None
        self.consecutive_no_changes = 0
        self.error_count = 0
        self.mission_files = {}
        self._prompt_cache = {}
        self._last_request_time = 0
        self._requests_this_minute = 0
        

    def _validate_run_conditions(self, prompt: str) -> bool:
        """
        Validate all conditions required for running Aider
        
        Args:
            prompt: Prompt to validate
            
        Returns:
            bool: True if all conditions are met
        """
        try:
            # Check mission directory
            if not os.path.exists(self.mission_dir):
                self.logger.log(f"[{self.name}] Mission directory not found: {self.mission_dir}")
                return False
                
            # Check permissions
            if not os.access(self.mission_dir, os.R_OK | os.W_OK):
                self.logger.log(f"[{self.name}] Insufficient permissions on mission directory")
                return False
                
            # Validate prompt
            if not prompt or not prompt.strip():
                self.logger.log(f"[{self.name}] Empty prompt provided")
                return False
                
            # Check for files to process
            if not self.mission_files:
                self.logger.log(f"[{self.name}] No files to process")
                return False
                
            # Check rate limiting
            if not self._check_rate_limit():
                self.logger.log(f"[{self.name}] Rate limit exceeded")
                return False
                
            return True
            
        except Exception as e:
            self.logger.log(f"[{self.name}] Error validating conditions: {str(e)}")
            return False


    def run_aider(self, prompt: str) -> Optional[str]:
        """Version diagnostique de run_aider"""
        try:
            self.logger.log(f"[{self.name}] 🔍 Début de run_aider()", 'debug')
        
            # Validation des préconditions
            if not self._validate_run_conditions(prompt):
                self.logger.log(f"[{self.name}] ❌ Conditions d'exécution non remplies", 'error')
                return None
        
            # Appel du parent avec logging
            result = self._run_aider(prompt)
        
            if result is None:
                self.logger.log(f"[{self.name}] ⚠️ Aucun résultat de run_aider", 'warning')
            else:
                self.logger.log(f"[{self.name}] ✅ run_aider exécuté avec succès", 'success')
        
            return result
    
        except Exception as e:
            self.logger.log(
                f"[{self.name}] 🔥 Erreur dans run_aider:\n"
                f"{traceback.format_exc()}", 
                'critical'
            )
            return None


    def _check_rate_limit(self) -> bool:
        """
        Check if we should wait before making another request
        
        Returns:
            bool: True if ok to proceed, False if should wait
        """
        current_time = time.time()
        
        # Reset counter if we're in a new minute
        if current_time - self._last_request_time > self.rate_limiter.time_window:
            self._requests_this_minute = 0
            
        # Check if we're approaching the limit
        if self._requests_this_minute >= self.rate_limiter.max_requests:
            wait_time = self.rate_limiter.get_wait_time()
            if wait_time > 0:
                self.logger.log(
                    f"[{self.name}] ⏳ Rate limit approaching. "
                    f"Waiting {wait_time:.1f}s",
                    'warning'
                )
                time.sleep(wait_time)
                self._requests_this_minute = 0
                
        self._last_request_time = current_time
        self._requests_this_minute += 1
        return True


    def _run_aider(self, prompt: str) -> Optional[str]:
        """Execute Aider with given prompt and handle all outcomes"""
        if not self._validate_run_conditions(prompt):
            return None

        try:
            # Check rate limiting
            if not self._check_rate_limit():
                self.logger.log(f"[{self.name}] Rate limit exceeded, skipping execution")
                return None

            # Log start of execution
            self.logger.log(f"[{self.name}] 🚀 Starting Aider execution", 'info')
            self.logger.log(f"[{self.name}] 📂 Mission directory: {self.mission_dir}", 'info')
            
            # Change to mission directory
            os.chdir(self.mission_dir)
            self.logger.log(f"[{self.name}] ✓ Changed to mission directory", 'info')

            # Build and validate command
            cmd = self.command_builder.build_command(
                prompt=prompt,
                files=list(self.mission_files.keys())
            )
            
            if not self.command_builder.validate_command(cmd):
                self.logger.log("Invalid command configuration", 'error')
                return None
                
            # Execute command with timeout
            with TimeoutManager.timeout(COMMAND_EXECUTION_TIMEOUT):
                process = self.command_builder.execute_command(cmd)

            # Parse output with timeout
            with TimeoutManager.timeout(OUTPUT_COLLECTION_TIMEOUT):
                output = self.output_parser.parse_output(process)
                
            # Handle known initialization errors gracefully
            initialization_errors = [
                "No Windows console found",
                "Failed to initialize console",
                "Could not initialize terminal"
            ]
            
            if output and any(err in output for err in initialization_errors):
                self.logger.log(
                    f"[{self.name}] Aider initialization error detected - will retry\n"
                    f"Error: {output}", 
                    'warning'
                )
                # Don't treat as interruption, just return None
                return None

            if output is None:
                self.logger.log(f"[{self.name}] ❌ No valid output from Aider")
                return None

            # Process file changes
            changes = self._process_file_changes(output)
            if changes['modified'] or changes['added'] or changes['deleted']:
                self.logger.log(
                    f"[{self.name}] Changes detected:\n"
                    f"Modified: {len(changes['modified'])} files\n"
                    f"Added: {len(changes['added'])} files\n"
                    f"Deleted: {len(changes['deleted'])} files"
                )
                
                # Update map after changes
                self._update_project_map()

            # Log the interaction using ChatLogger
            from utils.chat_logger import ChatLogger
            from utils.path_manager import PathManager
            
            # Use PathManager to get mission name and chats directory
            mission_name = os.path.basename(self.mission_dir)
            chat_logger = ChatLogger(mission_name)
            
            # Prepare files context with full content
            files_context = {
                filename: self.mission_files.get(filename, '') 
                for filename in list(changes['modified']) + list(changes['added'])
            }
            
            # Log agent interaction
            chat_logger.log_agent_interaction(
                agent_name=self.name,
                prompt=prompt,
                response=output,
                files_context=files_context
            )

            # Parse and log commits
            commit_logger = CommitLogger(self.logger)
            commit_logger.parse_commits(output, self.name)

            return output

        except TimeoutError:
            self.logger.log(f"[{self.name}] ⚠️ Operation timed out", 'warning')
            return None
            
        except Exception as e:
            # Don't treat console initialization errors as interruptions
            if "No Windows console found" in str(e):
                self.logger.log(f"[{self.name}] Aider console initialization error - will retry", 'error')
                return None
            self._handle_error('run_aider', e, {'prompt': prompt})
            return None
            
        finally:
            # Always try to restore original directory
            try:
                os.chdir(self.original_dir)
            except Exception as dir_error:
                self.logger.log(f"[{self.name}] Error restoring directory: {str(dir_error)}")

    def _process_file_changes(self, output: str) -> Dict[str, set]:
        """Process and track file changes from Aider output"""
        changes = {
            'modified': set(),
            'added': set(),
            'deleted': set()
        }
        
        try:
            for line in output.splitlines():
                if "Wrote " in line:
                    file_path = line.split("Wrote ")[1].split()[0]
                    changes['modified'].add(file_path)
                elif "Created " in line:
                    file_path = line.split("Created ")[1].split()[0]
                    changes['added'].add(file_path)
                elif "Deleted " in line:
                    file_path = line.split("Deleted ")[1].split()[0]
                    changes['deleted'].add(file_path)
                    
            return changes
            
        except Exception as e:
            self.logger.log(f"[{self.name}] Error processing changes: {str(e)}")
            return changes

    def _update_project_map(self) -> None:
        """Update project map after file changes"""
        try:
            from services import init_services
            services = init_services(None)
            services['map_service'].update_map()
            self.logger.log(f"[{self.name}] Map updated successfully")
        except Exception as e:
            self.logger.log(f"[{self.name}] Error updating map: {str(e)}")

    def get_prompt(self) -> Optional[str]:
        """Get prompt with caching"""
        return self.prompt_handler.get_prompt(self.prompt_file)
        
    def save_prompt(self, content: str) -> bool:
        """Save new prompt content"""
        return self.prompt_handler.save_prompt(self.prompt_file, content)

    def _handle_error(self, operation: str, error: Exception, context: Dict = None):
        """Centralised error handling"""
        try:
            error_details = {
                'agent': self.name,
                'operation': operation,
                'mission_dir': self.mission_dir,
                'context': context or {}
            }
            
            ErrorHandler.handle_error(
                error,
                log_level='error',
                additional_info=error_details
            )
            
        except Exception as e:
            self.logger.log(f"Error in error handler: {str(e)}", 'error')

    def stop(self):
        """Stop method to ensure cleanup"""
        try:
            # Call cleanup first
            self.cleanup()
            
            # Then handle regular stop logic
            self.running = False
            self.logger.log(f"[{self.name}] 🛑 Agent stopped")
            
        except Exception as e:
            self.logger.log(f"[{self.name}] ❌ Error stopping agent: {str(e)}")

    def run(self):
        """Main execution loop for the agent"""
        try:
            self.logger.log(f"[{self.name}] 🚀 Starting agent run loop", 'info')
            
            # Set running flag to True when starting
            self.running = True
            
            while self.running:
                try:
                    # Validate mission directory
                    if not os.path.exists(self.mission_dir):
                        self.logger.log(f"[{self.name}] ❌ Mission directory not found: {self.mission_dir}", 'error')
                        time.sleep(60)
                        continue

                    # Update file list
                    self.list_files()
                    
                    # Get current prompt
                    prompt = self.get_prompt()
                    if not prompt:
                        self.logger.log(f"[{self.name}] ⚠️ No prompt available, skipping run", 'warning')
                        time.sleep(60)
                        continue
                        
                    # Run Aider with current prompt
                    result = self.run_aider(prompt)
                    
                    # Update state based on result
                    self.last_run = datetime.now()
                    if result:
                        self.last_change = datetime.now()
                        self.consecutive_no_changes = 0
                    else:
                        self.consecutive_no_changes += 1
                        
                    # Calculate and wait for next interval
                    interval = self.calculate_dynamic_interval()
                    self.logger.log(f"[{self.name}] Waiting {interval}s before next run", 'info')
                    time.sleep(interval)
                    
                except Exception as loop_error:
                    self.logger.log(f"[{self.name}] ❌ Error in run loop: {str(loop_error)}", 'error')
                    time.sleep(5)  # Brief pause before retrying

            self.logger.log(f"[{self.name}] Run loop ended", 'info')
            
        except Exception as e:
            self.logger.log(f"[{self.name}] Critical error in run: {str(e)}", 'error')
            self.running = False
            
        finally:
            # Ensure cleanup happens
            self.cleanup()


    def _build_prompt(self, context: dict = None) -> str:
        """
        Build the complete prompt with context.
        
        Args:
            context (dict, optional): Additional context to include in prompt
            
        Returns:
            str: Complete formatted prompt
        """
        try:
            # Get base prompt content
            prompt_content = self.get_prompt()
            if not prompt_content:
                raise ValueError("No prompt content available")
                
            # If no context provided, return base prompt
            if not context:
                return prompt_content
                
            # Format mission files info
            files_info = self._format_mission_files(context)
            
            # Add agent status info
            status_info = {
                'last_run': self.last_run.isoformat() if self.last_run else 'Never',
                'last_change': self.last_change.isoformat() if self.last_change else 'Never',
                'consecutive_no_changes': self.consecutive_no_changes,
                'current_interval': self.calculate_dynamic_interval()
            }
            
            # Combine all context
            full_context = {
                'files': files_info,
                'status': status_info,
                **context  # Include any additional context
            }
            
            # Format prompt with context
            return prompt_content.format(**full_context)
            
        except Exception as e:
            self.logger(f"Error building prompt: {str(e)}")
            return self.prompt  # Fallback to default prompt
        
    def _handle_output_line(self, line: str) -> None:
        """
        Process a single line of Aider output
        
        Args:
            line: Output line to process
        """
        try:
            # Skip empty lines
            if not line.strip():
                return
                
            # Parse different line types
            if "Wrote " in line:
                self._handle_file_modification(line)
            elif "Commit" in line:
                self._handle_commit_message(line)
            elif self._is_error_message(line):
                self._handle_error_message(line)
            else:
                # Log regular output
                self.logger.log(f"[{self.name}] 📝 {line}", 'debug')
                
        except Exception as e:
            self.logger.log(f"[{self.name}] Error processing output line: {str(e)}")

    def _handle_file_modification(self, line: str) -> None:
        """
        Handle file modification output
        
        Args:
            line: Output line containing file modification
        """
        try:
            file_path = line.split("Wrote ")[1].split()[0]
            self.logger.log(f"[{self.name}] ✍️ Modified: {file_path}", 'info')
            
            # Track modification
            if hasattr(self, 'modified_files'):
                self.modified_files.add(file_path)
                
        except Exception as e:
            self.logger.log(f"[{self.name}] Error handling file modification: {str(e)}")

    def _handle_commit_message(self, line: str) -> None:
        """
        Handle commit message output
        
        Args:
            line: Output line containing commit message
        """
        try:
            # Extract commit hash and message
            parts = line.split()
            commit_hash = parts[1]
            message = ' '.join(parts[2:])
            
            # Detect commit type
            commit_type = None
            for known_type in self.output_parser.COMMIT_ICONS:
                if message.lower().startswith(f"{known_type}:"):
                    commit_type = known_type
                    message = message[len(known_type)+1:].strip()
                    break
                    
            # Get icon and log
            icon = self.output_parser.COMMIT_ICONS.get(commit_type, '🔨')
            self.logger.log(f"[{self.name}] {icon} {commit_hash}: {message}", 'success')
            
        except Exception as e:
            self.logger.log(f"[{self.name}] Error handling commit message: {str(e)}")

    def _handle_error_message(self, line: str) -> None:
        """
        Handle error message output
        
        Args:
            line: Output line containing error
        """
        self.logger.log(f"[{self.name}] ❌ {line}", 'error')
        self.error_count += 1

def list_files(self) -> None:
    """List and track files that this agent should monitor"""
    try:
        # Use FileHandler to list files in mission directory
        file_handler = FileHandler(self.mission_dir, self.logger)
        self.mission_files = file_handler.list_files()
        
        # Log files being monitored
        if self.mission_files:
            self.logger.log(
                f"[{self.name}] Monitoring {len(self.mission_files)} files:\n" + 
                "\n".join(f"  - {os.path.relpath(f, self.mission_dir)}" for f in self.mission_files.keys()), 
                'info'
            )
        else:
            self.logger.log(
                f"[{self.name}] No files found to monitor in {self.mission_dir}", 
                'warning'
            )
            
    except Exception as e:
        self.logger.log(
            f"[{self.name}] Error listing files: {str(e)}", 
            'error'
        )
