"""
AiderAgent - Core implementation of Aider-based agent functionality
"""
import os
import sys
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
            wait_time = self.rate_limiter.get_backoff_time()  # Use exponential backoff
            if wait_time > 0:
                self.logger.log(
                    f"[{self.name}] ⏳ Rate limit reached. "
                    f"Backing off for {wait_time:.1f}s",
                    'warning'
                )
                time.sleep(wait_time)
                self._requests_this_minute = 0
                return False  # Signal that we hit the limit
                
        self._last_request_time = current_time
        self._requests_this_minute += 1
        return True


    def _run_aider(self, prompt: str) -> Optional[str]:
        """Execute Aider command with streamed output processing"""
        try:
            # Validation des conditions préalables
            if not self._validate_run_conditions(prompt):
                return None

            # Construction et validation de la commande
            cmd = self.command_builder.build_command(
                prompt=prompt,
                files=list(self.mission_files.keys())
            )
            
            if not self.command_builder.validate_command(cmd):
                return None
                
            # Exécution avec gestion des timeout
            with TimeoutManager.timeout(COMMAND_EXECUTION_TIMEOUT):
                process = self.command_builder.execute_command(cmd)

            # Collection de la sortie
            with TimeoutManager.timeout(OUTPUT_COLLECTION_TIMEOUT):
                output = self.output_parser.parse_output(process)

            # Log interaction if we have output
            if output:
                self.logger.log("📝 Processing agent interaction for logging...")
                
                # Create files context
                files_context = {}
                for file_path in self.mission_files.keys():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            files_context[file_path] = content
                            self.logger.log(f"📄 Added file to context: {file_path}")
                    except Exception as e:
                        self.logger.log(f"❌ Error reading file for context: {str(e)}", 'error')

                # Get mission name from directory
                mission_name = os.path.basename(self.mission_dir)
                self.logger.log(f"📁 Using mission name: {mission_name}")

                # Log via ChatLogger
                try:
                    from utils.chat_logger import ChatLogger
                    chat_logger = ChatLogger(mission_name)
                    success = chat_logger.log_agent_interaction(
                        agent_name=self.name,
                        prompt=prompt,
                        response=output,
                        files_context=files_context
                    )
                    if success:
                        self.logger.log("✅ Successfully logged agent interaction")
                    else:
                        self.logger.log("⚠️ Failed to log agent interaction", 'warning')
                except Exception as e:
                    self.logger.log(f"❌ Error logging interaction: {str(e)}", 'error')

            return output

        except Exception as e:
            # Gestion des erreurs connues d'Aider
            known_errors = [
                "Can't initialize prompt toolkit",
                "No Windows console found",
                "aider.chat/docs/troubleshooting/edit-errors.html"
            ]
            if any(err in str(e) for err in known_errors):
                self.logger.log(
                    f"[{self.name}] Aider initialization warning - skipping", 
                    'debug'
                )
                return None
            
            # Gestion des autres exceptions
            self._handle_error('run_aider', e, {'prompt': prompt})
            return None
            
        finally:
            # Toujours restaurer le répertoire original
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

    def _should_log_error(self, error_message: str) -> bool:
        """
        Determine if an error message should be logged
        
        Args:
            error_message: Error message to check
        
        Returns:
            bool: Whether the message should be logged
        """
        # Liste des messages à ignorer
        ignored_messages = [
            "Can't initialize prompt toolkit: No Windows console found",
            "https://aider.chat/docs/troubleshooting/edit-errors.html"
        ]
        
        return not any(ignored_msg in error_message for ignored_msg in ignored_messages)

    def _handle_error(self, operation: str, error: Exception, context: Dict = None):
        """Centralised error handling"""
        try:
            error_message = str(error)
            
            # Utiliser le filtre avant de logger
            if self._should_log_error(error_message):
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

    def _is_error_message(self, line: str) -> bool:
        """
        Check if line contains error message
        
        Args:
            line: Output line to check
            
        Returns:
            bool: True if line contains error
        """
        # Documentation links should not be treated as errors
        if "documentation:" in line.lower():
            return False
            
        error_indicators = [
            'error',
            'exception', 
            'failed',
            'can\'t initialize',
            'fatal:',
            'permission denied'
        ]
        return any(indicator in line.lower() for indicator in error_indicators)

    def list_files(self) -> None:
        """List and track files that this agent should monitor"""
        try:
            # Use FileHandler to list files in mission directory
            file_handler = FileHandler(self.mission_dir, self.logger)
            self.mission_files = file_handler.list_files()
                
        except Exception as e:
            self.logger.log(
                f"[{self.name}] Error listing files: {str(e)}", 
                'error'
            )
