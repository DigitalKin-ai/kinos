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
from agents.aider.command_builder import AiderCommandBuilder
from agents.aider.output_parser import AiderOutputParser
from agents.utils.encoding import configure_encoding, detect_file_encoding, normalize_encoding
from agents.utils.rate_limiter import RateLimiter
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
from agents.base.file_handler import FileHandler
from agents.base.prompt_handler import PromptHandler
from utils.path_manager import PathManager

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
        self.rate_limiter = RateLimiter(max_requests=50, time_window=60)
        self.file_handler = FileHandler(self.mission_dir, self.logger)
        self.prompt_handler = PromptHandler(self.logger)
        
        # Store original directory
        self.original_dir = os.getcwd()
        
        try:
            # Initialize logger with thread-safe configuration
            from utils.logger import Logger
            import threading
            self._log_lock = threading.Lock()
            self.logger = Logger()
            
            # Initialize core attributes
            self.name = config.get("name")
            if not self.name:
                raise ValueError("name must be provided in config")
                
            self.mission_dir = config.get("mission_dir")
            if not self.mission_dir:
                raise ValueError("mission_dir must be provided in config")

            # Store original directory
            self.original_dir = os.getcwd()
            
            # Initialize state tracking
            self.running = False
            self.last_run = None
            self.last_change = None
            self.consecutive_no_changes = 0
            self.mission_files = {}
            self._prompt_cache = {}
            
            # Load prompt file path
            self.prompt_file = config.get("prompt_file")
            self.prompt = config.get("prompt", "")

            # Configure UTF-8 encoding
            self._configure_encoding()
            
            with self._log_lock:
                self.logger.log(f"[{self.name}] Initialized as {self.name}")
            
            self._last_request_time = 0
            self._requests_this_minute = 0
            self._rate_limit_window = 60  # 1 minute
            self._max_requests_per_minute = 50  # Adjust based on your rate limit
                              
        except Exception as e:
            print(f"Error during initialization: {str(e)}")
            raise
        

    def _log(self, message: str, level: str = 'info') -> None:
        """Centralized logging method"""
        if hasattr(self, 'logger'):
            self.logger.log(message, level)
        else:
            print(f"[{level.upper()}] {message}")

    def _get_relative_file_path(self, file_path: str) -> str:
        """Get relative path from mission directory"""
        try:
            return os.path.relpath(file_path, self.mission_dir)
        except Exception as e:
            self.logger(f"Error getting relative path: {str(e)}")
            return file_path


    def run_aider(self, prompt: str) -> Optional[str]:
        """Version diagnostique de run_aider"""
        try:
            self.logger.log(f"[{self.name}] 🔍 Début de run_aider()", 'debug')
        
            # Validation des préconditions
            if not self._validate_run_conditions(prompt):
                self._log(f"[{self.name}] ❌ Conditions d'exécution non remplies", 'error')
                return None
        
            # Appel du parent avec logging
            result = self._run_aider(prompt)
        
            if result is None:
                self._log(f"[{self.name}] ⚠️ Aucun résultat de run_aider", 'warning')
            else:
                self._log(f"[{self.name}] ✅ run_aider exécuté avec succès", 'success')
        
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
        Returns: True if ok to proceed, False if should wait
        """
        current_time = time.time()
        
        # Reset counter if we're in a new minute
        if current_time - self._last_request_time > self._rate_limit_window:
            self._requests_this_minute = 0
            
        # Check if we're approaching the limit
        if self._requests_this_minute >= self._max_requests_per_minute:
            wait_time = self._rate_limit_window - (current_time - self._last_request_time)
            if wait_time > 0:
                self._log(
                    f"[{self.name}] ⏳ Approaching rate limit. "
                    f"Waiting {wait_time:.1f}s before next request.",
                    'warning'
                )
                time.sleep(wait_time)
                self._requests_this_minute = 0
                
        self._last_request_time = current_time
        self._requests_this_minute += 1
        return True


    def _run_aider(self, prompt: str) -> Optional[str]:
        """Execute Aider with given prompt and handle all outcomes"""
        if not self._validate_run_input(prompt):
            return None

        try:
            # Log start of execution
            self._log(f"[{self.name}] 🚀 Starting Aider execution")
            self._log(f"[{self.name}] 📂 Mission directory: {self.mission_dir}")
            
            # Validate mission directory exists and is accessible
            if not os.path.exists(self.mission_dir):
                self._log(f"[{self.name}] ❌ Mission directory not found: {self.mission_dir}")
                return None

            # Build command with builder
            cmd = self.command_builder.build_command(
                prompt=prompt,
                files=list(self.mission_files.keys())
            )
            
            # Validate command
            if not self.command_builder.validate_command(cmd):
                self.logger.log("Invalid command configuration", 'error')
                return None
                
            # Execute command
            process = self.command_builder.execute_command(cmd)
            
            # Parse output
            return self.output_parser.parse_output(process)
            
        except Exception as e:
            self._handle_error('run_aider', e, {'prompt': prompt})
            return None

        # Validate mission directory exists and is accessible
        if not os.path.exists(self.mission_dir):
            self._log(f"[{self.name}] ❌ Mission directory not found: {self.mission_dir}")
            return None
            
        if not os.access(self.mission_dir, os.R_OK | os.W_OK):
                    self._log(f"[{self.name}] ❌ Insufficient permissions for: {self.mission_dir}")
                    return None

                try:
                    # Change to mission directory
                    os.chdir(self.mission_dir)
                    self._log(f"[{self.name}] ✓ Changed to mission directory")

                    # Build command
                    cmd = [
                        "aider",
                        "--model", "claude-3-5-haiku-20241022",
                        "--yes-always",
                        "--cache-prompts",
                        "--no-pretty",
                        "--architect"
                    ]

                    # Read .gitignore patterns
                    gitignore_patterns = []
                    gitignore_path = os.path.join(self.mission_dir, '.gitignore')
                    if os.path.exists(gitignore_path):
                        try:
                            with open(gitignore_path, 'r', encoding='utf-8') as f:
                                gitignore_patterns = f.readlines()
                            gitignore_patterns = [p.strip() for p in gitignore_patterns if p.strip() and not p.startswith('#')]
                            from pathspec import PathSpec
                            from pathspec.patterns import GitWildMatchPattern
                            spec = PathSpec.from_lines(GitWildMatchPattern, gitignore_patterns)
                        except Exception as e:
                            self.logger.log(f"[{self.name}] Warning reading .gitignore: {str(e)}", 'warning')
                            spec = None
                    else:
                        spec = None
                except Exception as e:
                    self._log(f"[{self.name}] ❌ Error during setup: {str(e)}")
                    return None

                # Add files, respecting .gitignore
                files_added = []
                for file_path in self.mission_files:
                    try:
                        rel_path = os.path.relpath(file_path, self.mission_dir)
                        
                        # Skip if file matches gitignore patterns
                        if spec and spec.match_file(rel_path):
                            self.logger.log(
                                f"[{self.name}] Skipping ignored file: {rel_path}", 
                                'debug'
                            )
                            continue

                        # Only add if file exists and is in mission directory
                        if os.path.exists(os.path.join(self.mission_dir, rel_path)):
                            cmd.extend(["--file", rel_path])
                            files_added.append(rel_path)
                            self.logger.log(f"[{self.name}] ➕ Added file: {rel_path}")
                    except Exception as e:
                        self.logger.log(f"[{self.name}] ⚠️ Error adding file {file_path}: {str(e)}")

                if not files_added:
                    self._log(f"[{self.name}] ⚠️ No files added to command")
                    return None
                
                # Add the message/prompt
                cmd.extend(["--message", prompt])

                # Set environment variables for encoding
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                
                self._log(f"[{self.name}] 🚀 Lancement Aider...")
            
                # Validate command before execution
                try:
                    import shutil
                    aider_path = shutil.which('aider')
                    if not aider_path:
                        self._log(f"[{self.name}] ❌ Aider command not found in PATH", 'error')
                        return None
                        
                    self._log(f"[{self.name}] ✓ Found Aider at: {aider_path}", 'debug')
                    
                    # Test if we can access the mission directory
                    if not os.access(self.mission_dir, os.R_OK | os.W_OK):
                        self._log(
                            f"[{self.name}] ❌ Cannot access mission directory: {self.mission_dir}", 
                            'error'
                        )
                        return None
                        
                except Exception as e:
                    self._log(f"[{self.name}] ❌ Command validation failed: {str(e)}", 'error')
                    return None

                # Set timeout duration (5 minutes)
                TIMEOUT_SECONDS = 300

                # Execute Aider with output streaming
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Redirect stderr to stdout
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    env=env,
                    bufsize=1
                )

                # Initialize output collection
                output_lines = []
                error_detected = False
                
                # Read output while process is running
                while True:
                    try:
                        line = process.stdout.readline()
                        if not line and process.poll() is not None:
                            break
                            
                        line = line.rstrip()
                        if line:
                            # Handle Windows console warning
                            if "No Windows console found" in line:
                                self._log(
                                    f"[{self.name}] ⚠️ Windows console initialization warning:\n"
                                    f"This is a known issue and doesn't affect functionality.\n"
                                    f"Original message: {line}",
                                    'warning'
                                )
                                continue

                            # Commit type icons with descriptions
                            COMMIT_ICONS = {
                                'feat': '✨',     # New feature
                                'fix': '🐛',      # Bug fix
                                'docs': '📚',     # Documentation
                                'style': '💎',    # Style/formatting
                                'refactor': '♻️',  # Refactoring
                                'perf': '⚡️',     # Performance
                                'test': '🧪',     # Tests
                                'build': '📦',    # Build/dependencies
                                'ci': '🔄',       # CI/CD
                                'chore': '🔧',    # Maintenance
                                'revert': '⏪',    # Revert changes
                                'merge': '🔗',    # Merge changes
                                'update': '📝',   # Content updates
                                'add': '➕',      # Add content/files
                                'remove': '➖',    # Remove content/files
                                'move': '🚚',     # Move/rename content
                                'cleanup': '🧹',  # Code cleanup
                                'format': '🎨',   # Formatting changes
                                'optimize': '🚀'  # Optimizations
                            }

                            # Log raw output for debugging
                            self._log(f"[{self.name}] 📝 Raw output: {line}", 'debug')

                            # Parse commit messages - more robust
                            if "Commit" in line:
                                try:
                                    # Extract commit hash and message
                                    commit_hash = line.split()[1]
                                    message = ' '.join(line.split()[2:])
                                    
                                    # Detect commit type from message
                                    commit_type = None
                                    for known_type in COMMIT_ICONS.keys():
                                        if message.lower().startswith(f"{known_type}:"):
                                            commit_type = known_type
                                            message = message[len(known_type)+1:].strip()
                                            break
                                    
                                    # Get appropriate icon
                                    icon = COMMIT_ICONS.get(commit_type, '🔨') if commit_type else '🔨'
                                    
                                    # Log with consistent format
                                    self.logger.log(
                                        f"[{self.name}] {icon} {commit_hash}: {message}",
                                        'success'
                                    )
                                        
                                except Exception as e:
                                    # Fallback if parsing fails
                                    self._log(f"[{self.name}] 🔨 {line}", 'success')
                            else:
                                # Handle non-commit lines
                                lower_line = line.lower()
                                is_error = any(err in lower_line for err in [
                                    'error', 'exception', 'failed', 'can\'t initialize'
                                ])
                                
                                if is_error:
                                    self._log(f"[{self.name}] ❌ {line}", 'error')
                                    error_detected = True
                                else:
                                    self._log(f"[{self.name}] 📝 {line}", 'info')
                            
                            output_lines.append(line)
                            
                    except Exception as e:
                        self._log(f"[{self.name}] Error reading output: {str(e)}")
                        continue

                # Get return code with timeout handling
                try:
                    with TimeoutManager.timeout(DEFAULT_TIMEOUT):
                        return_code = process.wait()
                except TimeoutError:
                    process.kill()
                    self._log(
                        f"[{self.name}] ⚠️ Process timed out after {DEFAULT_TIMEOUT} seconds", 
                        'warning'
                    )
                    return None
                
                # Get any remaining output with timeout handling
                try:
                    with TimeoutManager.timeout(OUTPUT_COLLECTION_TIMEOUT):
                        remaining_out, remaining_err = process.communicate()
                        if remaining_out:
                            for line in remaining_out.splitlines():
                                if line.strip():
                                    print(f"[{self.name}] {line}")
                                    output_lines.append(line)
                        if remaining_err:
                            for line in remaining_err.splitlines():
                                if line.strip():
                                    print(f"[{self.name}] ⚠️ {line}")
                                    output_lines.append(f"ERROR: {line}")
                except TimeoutError:
                    process.kill()
                    self._log(f"[{self.name}] Timeout collecting remaining output")

                # Combine all output
                full_output = "\n".join(output_lines)

                # Log processing results
                self._log(
                    f"[{self.name}] 🔄 Processing complete:\n"
                    f"Return code: {return_code}\n"
                    f"Output length: {len(full_output) if full_output else 0} chars\n"
                    f"Current directory: {os.getcwd()}",
                    'debug'
                )
                
                # Track modified files from output
                modified_files = set()
                for line in output_lines:
                    if "Wrote " in line and ".md" in line:
                        try:
                            modified_file = line.split("Wrote ")[1].split()[0]
                            modified_files.add(modified_file)
                        except:
                            pass

                # If execution was successful, log the changes
                if return_code == 0 and full_output:
                    try:
                        # Read modified files content
                        files_context = {}
                        for file_path in modified_files:
                            try:
                                # Use relative path for reading
                                full_path = os.path.join(self.mission_dir, file_path)
                                if os.path.exists(full_path):
                                    with open(full_path, 'r', encoding='utf-8') as f:
                                        files_context[file_path] = f.read()
                            except Exception as e:
                                error_str = str(e).lower()
                                
                                # Detect Anthropic rate limit errors
                                if any(msg in error_str for msg in ['rate limit', 'too many requests', '429']):
                                    if self._handle_rate_limit_error(attempt, max_attempts):
                                        attempt += 1
                                        continue
                                    else:
                                        self._log(f"[{self.name}] ❌ Abandoning after {max_attempts} rate limit retries")
                                        return None
                                
                                # For other errors, log and continue
                                self._log(f"[{self.name}] ❌ Error reading modified file {file_path}: {str(e)}")
                                continue

                        # Add original files if not already included
                        for file_path in self.mission_files:
                            rel_path = os.path.relpath(file_path, self.mission_dir)
                            if rel_path not in files_context:
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        files_context[rel_path] = f.read()
                                except Exception as e:
                                    error_str = str(e).lower()
                                    
                                    # Detect Anthropic rate limit errors
                                    if any(msg in error_str for msg in ['rate limit', 'too many requests', '429']):
                                        if self._handle_rate_limit_error(attempt, max_attempts):
                                            attempt += 1
                                            continue
                                        else:
                                            self._log(f"[{self.name}] ❌ Abandoning after {max_attempts} rate limit retries")
                                            return None
                                    
                                    # For other errors, log and continue
                                    self._log(f"[{self.name}] ❌ Error reading original file {file_path}: {str(e)}")
                                    continue

                        # Only proceed if we have files to save
                        if files_context:
                            # Log the changes
                            self.logger.log(
                                f"Files modified:\n" + "\n".join(files_context.keys()),
                                'info'
                            )

                    except Exception as e:
                        error_str = str(e).lower()
                        
                        # Detect Anthropic rate limit errors
                        if any(msg in error_str for msg in ['rate limit', 'too many requests', '429']):
                            if self._handle_rate_limit_error(attempt, max_attempts):
                                attempt += 1
                                continue
                            else:
                                self._log(f"[{self.name}] ❌ Abandoning after {max_attempts} rate limit retries")
                                return None
                        
                        # For other errors, log and continue
                        self._log(f"[{self.name}] ❌ Error reading files: {str(e)}")
                
                # Log completion status
                if return_code != 0:
                    self._log(
                        f"[{self.name}] ❌ Aider process failed (code: {return_code})\n"
                        f"Last few lines of output:\n" + 
                        "\n".join(output_lines[-5:]),  # Show last 5 lines
                        'error'
                    )
                    return None
                elif error_detected:
                    self._log(
                        f"[{self.name}] ⚠️ Aider completed with warnings\n"
                        f"Last few lines of output:\n" + 
                        "\n".join(output_lines[-5:]),
                        'warning'
                    )
                
                # Combine output
                full_output = "\n".join(output_lines)
                if not full_output.strip():
                    self._log(f"[{self.name}] ⚠️ No output from Aider", 'warning')
                    return None
                    
                self._log(f"[{self.name}] ✅ Aider completed successfully", 'success')
                
                # Track modified files from output
                modified_files = set()
                for line in output_lines:
                    if "Wrote " in line and ".md" in line:
                        try:
                            modified_file = line.split("Wrote ")[1].split()[0]
                            modified_files.add(modified_file)
                        except:
                            pass

                # If execution was successful, save for fine-tuning
                if return_code == 0 and full_output:
                    try:
                        # Read modified files content
                        files_context = {}
                        for file_path in modified_files:
                            try:
                                # Use relative path for reading
                                full_path = os.path.join(self.mission_dir, file_path)
                                if os.path.exists(full_path):
                                    with open(full_path, 'r', encoding='utf-8') as f:
                                        files_context[file_path] = f.read()
                            except Exception as e:
                                self.logger.log(f"Error reading modified file {file_path}: {str(e)}", 'error')
                                continue

                        # Add original files if not already included
                        for file_path in self.mission_files:
                            rel_path = os.path.relpath(file_path, self.mission_dir)
                            if rel_path not in files_context:
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        files_context[rel_path] = f.read()
                                except Exception as e:
                                    self.logger.log(f"Error reading original file {file_path}: {str(e)}", 'error')
                                    continue

                        # Only proceed if we have files to save
                        if files_context:
                            # Log the changes
                            self.logger.log(
                                f"Files modified:\n" + "\n".join(files_context.keys()),
                                'info'
                            )

                    except Exception as e:
                        self._log(f"[{self.name}] Error saving to dataset: {str(e)}")

                # Return output if process succeeded
                if return_code == 0:
                    try:
                        # Update map after modifications
                        from services import init_services
                        services = init_services(None)
                        services['map_service'].update_map()
                        self._log(f"[{self.name}] Map updated successfully")
                    except Exception as e:
                        self._log(f"[{self.name}] Error updating map: {str(e)}")
                    return full_output
                else:
                    self._log(f"[{self.name}] Process failed with code {return_code}")
                    return None

        except Exception as e:
            self._log(f"[{self.name}] Error in _run_aider: {str(e)}")
            return None

    def list_files(self) -> None:
        """List all text files in mission directory"""
        self.mission_files = self.file_handler.list_files()

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
            self.prompt_handler._prompt_cache.clear()
            self.mission_files.clear()
            
            # Base cleanup
            super().cleanup()
            
        except Exception as e:
            self.logger.log(f"Error in cleanup: {str(e)}", 'error')

    def stop(self):
        """Stop method to ensure cleanup"""
        try:
            # Call cleanup first
            self.cleanup()
            
            # Then handle regular stop logic
            self.running = False
            self._log(f"[{self.name}] 🛑 Agent stopped")
            
        except Exception as e:
            self._log(f"[{self.name}] ❌ Error stopping agent: {str(e)}")

    def run(self):
        """Main execution loop for the agent"""
        try:
            self._log(f"[{self.name}] 🚀 Starting agent run loop")
            
            while self.running:
                try:
                    # Use configured mission directory
                    if not self.mission_dir:
                        self._log(f"[{self.name}] ❌ No mission directory configured")
                        time.sleep(60)
                        continue

                    # Validate mission directory
                    if not os.path.exists(self.mission_dir):
                        self._log(f"[{self.name}] ❌ Mission directory not found: {self.mission_dir}")
                        time.sleep(60)
                        continue

                    # Update file list
                    self.list_files()
                    
                    # Get current prompt
                    prompt = self.get_prompt()
                    if not prompt:
                        self._log(f"[{self.name}] ⚠️ No prompt available, skipping run")
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
                    time.sleep(interval)
                    
                except Exception as loop_error:
                    self._log(f"[{self.name}] ❌ Error in run loop: {str(loop_error)}")
                    time.sleep(5)  # Pause before retrying

            self._log(f"[{self.name}] Run loop ended")
            
        except Exception as e:
            self._log(f"[{self.name}] Critical error in run: {str(e)}")
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
