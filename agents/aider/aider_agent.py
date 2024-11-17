"""
AiderAgent - Core implementation of Aider-based agent functionality
"""
import os
import sys
import time
import subprocess
import traceback
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from agents.base.agent_base import AgentBase
from agents.base.file_handler import FileHandler
from utils.logger import Logger
from agents.aider.command_builder import AiderCommandBuilder
from agents.aider.output_parser import AiderOutputParser
from agents.utils.encoding import configure_encoding, detect_file_encoding, normalize_encoding
from agents.utils.rate_limiter import RateLimiter
from utils.commit_logger import CommitLogger
from agents.base.file_handler import FileHandler
from utils.path_manager import PathManager
from utils.error_handler import ErrorHandler
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
        # Fail fast - validate critical requirements first
        if not config:
            raise ValueError("Config is required")
        if 'team' not in config:
            raise ValueError("Team name is required in config")
        if 'name' not in config:
            raise ValueError("Agent name is required in config") 
        if 'services' not in config or not config['services']:
            raise ValueError("Required services not provided in config")

        try:
            # Check if this agent is already initialized for this team
            agent_key = f"{config['name']}_{config['team']}"
            if hasattr(AiderAgent, '_initialized_agents'):
                if agent_key in AiderAgent._initialized_agents:
                    raise RuntimeError(f"Agent {config['name']} already initialized for team {config['team']}")
            else:
                AiderAgent._initialized_agents = set()

            # Validate required config fields first
            required_fields = ['team', 'name', 'services', 'type', 'weight']
            missing_fields = [f for f in required_fields if f not in config]
            if missing_fields:
                raise ValueError(f"Missing required config fields: {', '.join(missing_fields)}")

            # Store original directory
            self.original_dir = os.getcwd()
            
            # Set core attributes before super().__init__
            self.team = config['team']
            self.name = config['name']
            self.services = config['services']
            
            # Get mission directory using PathManager - fail fast
            self.mission_dir = PathManager.get_team_path(self.team)
            if not os.path.exists(self.mission_dir):
                raise FileNotFoundError(f"Mission directory not found: {self.mission_dir}")
            
            # Update config with mission_dir
            config['mission_dir'] = self.mission_dir
            
            # Initialize parent with validated config
            super().__init__(config)
            
            # Configure components
            self._configure_encoding()
            self.command_builder = AiderCommandBuilder(self.name, self.team)
            self.output_parser = AiderOutputParser(self.logger, self.name)
            
            self.logger.log(f"[{self.name}] Initialized in team {self.team}")
            
            # Initialize rate limiter and file handler
            self.rate_limiter = RateLimiter(max_requests=50, time_window=60)
            self.file_handler = FileHandler(self.mission_dir, self.logger)
                
            # Get prompt file
            self.prompt_file = PathManager.get_prompt_file(self.name, self.team)
            if not self.prompt_file:
                raise ValueError(f"No prompt file found for agent {self.name}")
                    
            # Initialize state
            self._init_state()

            # Mark this agent as initialized
            AiderAgent._initialized_agents.add(agent_key)
                
        except Exception as e:
            logger = Logger()
            logger.log(f"[INIT] Error during initialization: {str(e)}", 'error')
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


    def _run_aider(self, instructions: str) -> str:
        """Execute Aider command with streamed output processing"""
        if not instructions:
            raise ValueError("Instructions cannot be empty")
        if not self.team:
            raise ValueError("Team name is required")
        if not self.name:
            raise ValueError("Agent name is required")

        # Get correct team path using PathManager
        team_path = PathManager.get_team_path(self.team)
        history_dir = os.path.join(team_path, "history")
        os.makedirs(history_dir, exist_ok=True)
        
        # Create history file paths
        chat_history_file = os.path.join(history_dir, f".aider.{self.name}.chat.history.md")
        input_history_file = os.path.join(history_dir, f".aider.{self.name}.input.history.md")

        # Build and validate command
        cmd = self.command_builder.build_command(
            instructions=instructions,
            files=list(self.mission_files.keys())
        )
        
        # Add history files
        cmd.extend([
            "--chat-history-file", chat_history_file,
            "--input-history-file", input_history_file
        ])

        # Execute command and return output - let errors propagate
        process = self.command_builder.execute_command(cmd)
        output = self.output_parser.parse_output(process)
        
        # Skip known benign messages
        if output and any(msg in output for msg in [
            "Can't initialize prompt toolkit",
            "No Windows console found", 
            "aider.chat/docs/troubleshooting/edit-errors.html",
            "[Errno 22] Invalid argument"
        ]):
            return ""
            
        # Update services if we got output
        if output:
            try:
                # Use existing services if available
                if self.services:
                    map_service = self.services['map_service']
                    dataset_service = self.services['dataset_service']
                else:
                    # Only initialize if needed
                    self.logger.log(f"[{self.name}] Warning: Falling back to service initialization", 'warning')
                    from services import init_services
                    self.services = init_services(None)
                    map_service = self.services['map_service']
                    dataset_service = self.services['dataset_service']
            
                # Update map
                map_service.update_map()
            
                # Get current file contents
                files_context = {}
                for file_path in self.mission_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            files_context[file_path] = f.read()
                    except Exception as e:
                        self.logger.log(f"[{self.name}] Error reading {file_path}: {str(e)}", 'warning')
            
                # Log interaction
                import asyncio
                asyncio.run(dataset_service.add_interaction_async(
                    instructions=instructions,
                    files_context=files_context,
                    aider_response=output
                ))
            
            except Exception as service_error:
                self.logger.log(f"[{self.name}] Error with services: {str(service_error)}", 'warning')
                
        try:
            # Execute command and return output - let errors propagate
            process = self.command_builder.execute_command(cmd)
            output = self.output_parser.parse_output(process)
            
            # Skip known benign messages
            if output and any(msg in output for msg in [
                "Can't initialize prompt toolkit",
                "No Windows console found", 
                "aider.chat/docs/troubleshooting/edit-errors.html",
                "[Errno 22] Invalid argument"
            ]):
                return ""
                
            # Update services if we got output
            if output:
                try:
                    # Use existing services if available
                    if self.services:
                        map_service = self.services['map_service']
                        dataset_service = self.services['dataset_service']
                    else:
                        # Only initialize if needed
                        self.logger.log(f"[{self.name}] Warning: Falling back to service initialization", 'warning')
                        from services import init_services
                        self.services = init_services(None)
                        map_service = self.services['map_service']
                        dataset_service = self.services['dataset_service']
                
                    # Update map
                    map_service.update_map()
                
                    # Get current file contents
                    files_context = {}
                    for file_path in self.mission_files:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                files_context[file_path] = f.read()
                        except Exception as e:
                            self.logger.log(f"[{self.name}] Error reading {file_path}: {str(e)}", 'warning')
                
                    # Log interaction
                    import asyncio
                    asyncio.run(dataset_service.add_interaction_async(
                        instructions=instructions,
                        files_context=files_context,
                        aider_response=output
                    ))
                
                except Exception as service_error:
                    self.logger.log(f"[{self.name}] Error with services: {str(service_error)}", 'warning')
                    
            return output
            
        except OSError as os_error:
            # Handle Windows stream error
            if "[Errno 22] Invalid argument" in str(os_error):
                return ""
            raise
            
        except Exception as e:
            # Log and continue
            self.logger.log(f"[{self.name}] Non-critical error: {str(e)}", 'warning')
            return ""
            
        finally:
            # Always restore original directory
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
        """Prevent agent from stopping"""
        pass  # Ne rien faire - empêcher l'arrêt

    def _truncate_history(self, content: str, max_chars: int = 25000) -> str:
        """Truncate history content to last N characters"""
        if len(content) <= max_chars:
            return content
        return content[-max_chars:]

    def _execute_agent_cycle(self):
        """Execute one cycle of the agent's main loop"""
        # Initialize result variable
        result = None

        try:
            # Validate required state first
            if not self.team:
                raise ValueError(f"[{self.name}] No team context available")
            if not self.services:
                raise ValueError(f"[{self.name}] No services available")
            if not self.mission_files:
                raise ValueError(f"[{self.name}] No files to monitor")

            self.logger.log(f"[{self.name}] Starting cycle for team: {self.team}", 'debug')

            # Read file contents into a new dictionary
            files_with_content = {}
            for file_path in self.mission_files.keys():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files_with_content[file_path] = f.read()
                except Exception as e:
                    self.logger.log(f"[{self.name}] Error reading {file_path}: {str(e)}", 'warning')
                    continue

            if not files_with_content:
                raise ValueError(f"[{self.name}] No readable files found")

            # Get current prompt using PathManager - fail fast if missing
            prompt_path = PathManager.get_prompt_file(self.name, self.team)
            if not prompt_path or not os.path.exists(prompt_path):
                # Create default prompt directory
                os.makedirs(os.path.dirname(prompt_path), exist_ok=True)
                
                # Create default aider prompt
                default_prompt = """# Aider Agent

You are an AI development assistant that helps implement requested changes.
Your role is to:
1. Understand the current state of files
2. Make specific, focused changes to progress the mission
3. Commit changes with clear messages

## Guidelines
- Make one focused change at a time
- Explain what you're changing and why
- Use clear commit messages
- Keep changes small and manageable

## Format
Always structure your responses as:
1. What you're going to change
2. Why you're making the change
3. How you'll implement it

## Rules
- Only modify files shown to you
- Make one change at a time
- Use clear commit messages
- Keep changes focused"""

                # Write default prompt
                with open(prompt_path, 'w', encoding='utf-8') as f:
                    f.write(default_prompt)
                    self.logger.log(f"[{self.name}] Created default prompt at {prompt_path}", 'info')

            # Read prompt content - fail fast if empty
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()

            if not prompt:
                raise ValueError(f"[{self.name}] Empty prompt file for team {self.team}")

            # Format context message with team info
            context_message = f"""You are {self.name}, working in team {self.team}, on the mission defined in demande.md.
Based on the current state of the files, choose ONE specific task to progress.

Current project files:
{self._format_files_context(files_with_content)}

Instructions:
1. Analyze the current state
2. Identify a clear next action
3. Describe the specific task in detail
4. Explain what files to modify
5. Keep it focused and achievable"""

            # Use stored model_router service with team context
            model_router = self.services['model_router']
            import asyncio
            model_response = asyncio.run(model_router.generate_response(
                messages=[{
                    "role": "user", 
                    "content": context_message,
                    "team": self.team
                }],
                system=prompt,
                max_tokens=1000
            ))

            if not model_response:
                raise ValueError(f"No response from model for team {self.team}")

            # Run Aider with generated instructions and team context
            try:
                # Change to team directory before running Aider
                team_dir = os.path.join(os.getcwd(), f"team_{self.team}")
                if os.path.exists(team_dir):
                    os.chdir(team_dir)
                result = self._run_aider(model_response)
            finally:
                # Always restore original directory
                os.chdir(self.original_dir)

        except Exception as e:
            self.logger.log(
                f"[{self.name}] 💥 Error in agent cycle:\n"
                f"Type: {type(e)}\n"
                f"Error: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}",
                'error'
            )
            return None

        # Update state based on result
        self.last_run = datetime.now()
        if result:
            self.last_change = datetime.now()
            self.consecutive_no_changes = 0
        else:
            self.consecutive_no_changes += 1

        return result


            
        # Process key files and remaining files
        # Initialize files context dictionary
        files_context = {}
        
        try:
            # Define key files
            key_files = {
                os.path.join(self.mission_dir, "map.md"): True,
                os.path.join(self.mission_dir, "todolist.md"): True,
                os.path.join(self.mission_dir, "demande.md"): True,
                os.path.join(self.mission_dir, "directives.md"): True
            }
            
            # Add key files first using full paths
            for file_path, _ in key_files.items():
                try:
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            files_context[file_path] = f.read()
                except Exception as e:
                    self.logger.log(f"[{self.name}] Error reading key file {file_path}: {str(e)}", 'warning')

            # Get remaining files - Use .gitignore patterns for filtering
            from pathspec import PathSpec
            from pathspec.patterns import GitWildMatchPattern

            # Load ignore patterns from .gitignore
            ignore_patterns = []
            gitignore_path = os.path.join(self.mission_dir, '.gitignore')
            if os.path.exists(gitignore_path):
                try:
                    with open(gitignore_path, 'r', encoding='utf-8') as f:
                        ignore_patterns = [
                            line.strip() for line in f.readlines()
                            if line.strip() and not line.startswith('#')
                        ]
                except Exception as e:
                    self.logger.log(f"[{self.name}] Error reading .gitignore: {str(e)}", 'warning')

            # Create PathSpec for pattern matching
            spec = PathSpec.from_lines(GitWildMatchPattern, ignore_patterns)

            # Filter files using gitignore patterns
            remaining_files = [
                f for f in self.mission_files.keys()
                if f not in key_files
                and not spec.match_file(os.path.relpath(f, self.mission_dir))
            ]

            if len(remaining_files) > 10:
                import random
                remaining_files = random.sample(remaining_files, 10)
                self.logger.log(f"[{self.name}] Sampling 10 random files from {len(remaining_files)} eligible files", 'debug')
        
            # Add selected files
            for file_path in remaining_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files_context[file_path] = f.read()
                except Exception as e:
                    self.logger.log(f"[{self.name}] Error reading file {file_path}: {str(e)}", 'warning')

        except Exception as e:
            self.logger.log(f"[{self.name}] Error processing remaining files: {str(e)}", 'warning')

            # Format context message
            context_message = f"""You are {self.name}, an agent working autonomously in the KinOS system, to achieve a mission.
Based on:
1. The system prompt defining my role and responsibilities ({self.name})
2. The Mission in demande.md
3. The chat history showing your previous instructions and Aider's productions
4. The current state of the project files shown below

Choose ONE specific, concrete task that needs to be done by the agent {self.name} to progress in the mission and explain it in detail so that Aider can implement it.
Focus on practical changes that move the project forward, directly related to demande.md

Current project files:
{self._format_files_context(files_context)}

Instructions:
1. Answer any outstanding question raised by Aider in the chat history
2. Analyze the current state and identify a clear next action, preferably different from what's in the chat history (we are following a "Breadth-first" development pattern)
3. Describe this specific task in detail
4. Explain what files need to be modified and how
5. Keep the task focused and achievable
6. Provide enough detail for Aider to implement it autonomously
7. Ask him specifically to do the task now, making decisions instead of asking for clarifications"""

            # Get model router and verify model
            model_router = self.services['model_router']
            if not model_router.is_model_available():
                self.logger.log(f"[{self.name}] No valid model configured", 'error')
                return None
                
            try:
                # Read prompt file content
                if isinstance(prompt, str) and os.path.exists(prompt):
                    with open(prompt, 'r', encoding='utf-8') as f:
                        prompt_content = f.read()
                    self.logger.log(f"[{self.name}] Loaded prompt content from {prompt}", 'debug')
                else:
                    raise ValueError(f"Invalid prompt file path: {prompt}")

                # Create messages array with only user and assistant roles
                messages = [{"role": "user", "content": context_message}]
            
                # Use model router with system prompt as top-level parameter
                import asyncio
                model_response = asyncio.run(model_router.generate_response(
                    messages=messages,  # Only user/assistant messages
                    system=prompt_content,  # System prompt as separate parameter
                    max_tokens=1000
                ))

                if not model_response:
                    raise ValueError("No response from model")
                
                self.logger.log(f"[{self.name}] Generated instructions:\n{model_response}", 'debug')
            
            except Exception as e:
                self.logger.log(f"[{self.name}] Error calling LLM: {str(e)}", 'error')
                return

            # Run Aider with generated instructions
            try:
                result = self._run_aider(model_response)
            except OSError as os_error:
                if "[Errno 22] Invalid argument" in str(os_error):
                    # Ignore this specific Windows error
                    self.logger.log(f"[{self.name}] Ignoring Windows stdout flush error", 'debug')
                    return
                else:
                    raise
            except Exception as e:
                # Ignore known Aider errors
                if any(err in str(e) for err in [
                    "Can't initialize prompt toolkit",
                    "No Windows console found",
                    "aider.chat/docs/troubleshooting/edit-errors.html"
                ]):
                    return
                raise

            # Update state based on result
            self.last_run = datetime.now()
            if result:
                self.last_change = datetime.now()
                self.consecutive_no_changes = 0
            else:
                self.consecutive_no_changes += 1

        except Exception as e:
            self.logger.log(
                f"[{self.name}] 💥 Comprehensive error in agent cycle:\n"
                f"Type: {type(e)}\n"
                f"Error: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}",
                'critical'
            )
            return None

    def run(self):
        """Execute one iteration of the agent's task"""
        # Validate mission directory first
        if not os.path.exists(self.mission_dir):
            raise FileNotFoundError(f"[{self.name}] Mission directory not found")

        self.logger.log(f"[{self.name}] 🔄 Starting agent iteration", 'debug')

        # Update file list - fail if no files found
        self.list_files()
        if not self.mission_files:
            raise ValueError(f"[{self.name}] No files to monitor")

        # Execute cycle and let errors propagate
        result = self._execute_agent_cycle()
        
        # Update state based on result
        self.last_run = datetime.now()
        if result:
            self.last_change = datetime.now()
            self.consecutive_no_changes = 0
        else:
            self.consecutive_no_changes += 1

        # Always ensure cleanup happens
        self.cleanup()

    def _format_files_context(self, files_context: Dict[str, str]) -> str:
        """
        Format files context into readable string with validation
        
        Args:
            files_context: Dictionary mapping filenames to content
            
        Returns:
            str: Formatted string with file content blocks
            
        Raises:
            TypeError: If inputs are not correct types
            ValueError: If inputs are empty or invalid
            FileNotFoundError: If files don't exist
        """
        if not isinstance(files_context, dict):
            raise TypeError("files_context must be a dictionary")
        if not files_context:
            raise ValueError("files_context cannot be empty")
        if not self.mission_dir:
            raise ValueError("mission_dir not set")

        formatted = []
        for filename, content in files_context.items():
            if not isinstance(filename, str):
                raise TypeError(f"Filename must be string, got {type(filename)}")
            if not isinstance(content, str):
                raise TypeError(f"Content must be string, got {type(content)}")
            if not os.path.exists(filename):
                raise FileNotFoundError(f"File not found: {filename}")
                
            rel_path = os.path.relpath(filename, self.mission_dir)
            formatted.append(f"File: {rel_path}\n```\n{content}\n```\n")
            
        return "\n".join(formatted)

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
