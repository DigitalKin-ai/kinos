"""
AiderCommandBuilder - Handles Aider command construction and execution
"""
import os
import subprocess
from typing import List, Dict, Any
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from utils.path_manager import PathManager

class AiderCommandBuilder:
    """Builds and executes Aider commands"""
    
    def __init__(self, agent_name: str):
        """Initialize with agent name"""
        self.agent_name = agent_name
        
        try:
            # Get services
            from services import init_services
            services = init_services(None)
            team_service = services['team_service']
            
            # Get active team info
            active_team = team_service.get_active_team()
            self.team = active_team.get('name', 'default')
            self.team_name = active_team.get('display_name', self.team.title())
            
            # Get mission directory from current working directory
            self.mission_dir = os.getcwd()
            
            # Initialize logger
            from utils.logger import Logger
            self.logger = Logger()
            self.logger.log(f"[{self.agent_name}] Team: {self.team_name} (ID: {self.team})", 'debug')
            
        except Exception as e:
            from utils.logger import Logger
            logger = Logger()
            logger.log(f"Error detecting team: {str(e)}", 'warning')
            self.team = 'default'
            self.team_name = 'Default Team'

    def get_model_args(self) -> List[str]:
        """Get model-specific command arguments"""
        try:
            # Get current model from ModelRouter
            from services import init_services
            services = init_services(None)
            model_router = services['model_router']
            current_model = model_router.current_model
            
            return [
                "--model", current_model,
                "--edit-format", "diff",
                "--yes-always",
                "--cache-prompts",
                "--no-pretty"
            ]
        except Exception:
            # Fallback to default model if ModelRouter not available
            return [
                "--model", "claude-3-5-haiku-20241022",
                "--edit-format", "diff",
                "--yes-always",
                "--cache-prompts",
                "--no-pretty"
            ]

    def get_file_args(self, files: List[str], ignore_patterns: List[str]) -> List[str]:
        """
        Get file-related command arguments
        
        Args:
            files: List of files to include
            ignore_patterns: List of patterns to ignore
            
        Returns:
            List of file arguments
        """
        from utils.path_manager import PathManager  # Move import here
        
        args = []
        
        # Filter ignored files first
        valid_files = [
            file for file in files 
            if not any(pattern in file for pattern in ignore_patterns)
        ]
        
        # Define read-only files using PathManager
        team_path = PathManager.get_team_path(self.team)
        readonly_files = [
            os.path.join(team_path, "demande.md"),
            os.path.join(team_path, "map.md")
        ]
        
        # Get agent's prompt file path using PathManager
        prompt_path = PathManager.get_prompt_file(self.agent_name, self.team)
        
        # Remove readonly files from valid_files if present to avoid duplicates
        valid_files = [f for f in valid_files if f not in readonly_files]
        
        # Limit remaining files to 10 random if needed
        if len(valid_files) > 10:
            import random
            valid_files = random.sample(valid_files, 10)
        
        # Add read-only files first with --read flag
        for file in readonly_files:
            if os.path.exists(file):  # Only add if file exists
                args.extend(["--read", file])
            
        # Add agent prompt as read-only if found
        if prompt_path and os.path.exists(prompt_path):
            args.extend(["--read", prompt_path])
            
        # Add key files that should be editable
        key_files = [
            os.path.join(team_path, "todolist.md"),
            os.path.join(team_path, "directives.md")
        ]
        for file in key_files:
            if os.path.exists(file):  # Only add if file exists
                args.extend(["--file", file])
            
        # Add selected files
        for file in valid_files:
            args.extend(["--file", file])
            
        return args

    def validate_command(self, cmd: List[str]) -> bool:
        """
        Validate command before execution
        
        Args:
            cmd: Command arguments list
            
        Returns:
            bool: True if command is valid
        """
        try:
            # Check for required arguments
            required = ["--model", "--file", "--message"]
            for arg in required:
                if arg not in cmd:
                    return False
                    
            # Validate model argument
            model_idx = cmd.index("--model")
            if len(cmd) <= model_idx + 1:
                return False
                
            # Validate files exist
            file_indices = [i for i, arg in enumerate(cmd) if arg == "--file"]
            for idx in file_indices:
                if len(cmd) <= idx + 1:
                    return False
                file_path = cmd[idx + 1]
                if not os.path.exists(file_path):
                    return False
                    
            return True
            
        except Exception:
            return False

    def build_command(self, instructions: str, files: List[str]) -> List[str]:
        """Build Aider command with arguments"""
        cmd = ["python", "-m", "aider"]
        
        # Add model args
        cmd.extend(self.get_model_args())
        cmd.extend(self.get_file_args(files, self.get_ignore_patterns(self.mission_dir)))
        
        # Create team directory path in mission directory
        team_dir = os.path.join(self.mission_dir, f"team_{self.team}")
        history_dir = os.path.join(team_dir, "history")
        
        # Create directories
        os.makedirs(history_dir, exist_ok=True)
        
        # Create history files with empty content if they don't exist
        chat_history = os.path.join(history_dir, f".aider.{self.agent_name}.chat.history.md")
        input_history = os.path.join(history_dir, f".aider.{self.agent_name}.input.history.md")
        
        for history_file in [chat_history, input_history]:
            if not os.path.exists(history_file):
                try:
                    with open(history_file, 'w', encoding='utf-8') as f:
                        f.write("")
                    self.logger.log(f"Created history file: {history_file}", 'debug')
                except Exception as e:
                    self.logger.log(f"Error creating history file {history_file}: {str(e)}", 'error')
        
        # Add history file arguments
        cmd.extend([
            "--chat-history-file", chat_history,
            "--input-history-file", input_history
        ])
        
        # Add instructions
        stringified_instructions = instructions.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        cmd.extend(["--message", f'"{stringified_instructions} ALWAYS DIRECTLY PROCEED WITH THE MODIFICATIONS, USING THE SEARCH/REPLACE FORMAT."'])
        
        self.logger.log(f"Aider command: {cmd}", 'info')

        if not self.validate_command(cmd):
            print(f"DEBUG: Invalid command configuration for {self.agent_name}")
            raise ValueError("Invalid command configuration")
            
        return cmd
        
    def execute_command(self, cmd: List[str]) -> subprocess.Popen:
        """
        Execute Aider command
        
        Args:
            cmd: Command arguments list
            
        Returns:
            subprocess.Popen: Process handle
        """
        # Set environment
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Execute with output streaming
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env,
            bufsize=1
        )
        
    def get_ignore_patterns(self, directory: str) -> List[str]:
        """
        Get ignore patterns from .gitignore and .aiderignore
        
        Args:
            directory: Directory to check for ignore files
            
        Returns:
            List of ignore patterns
        """
        patterns = []
        
        # Check both .gitignore and .aiderignore
        for ignore_file in ['.gitignore', '.aiderignore']:
            ignore_path = os.path.join(directory, ignore_file)
            if os.path.exists(ignore_path):
                try:
                    with open(ignore_path, 'r', encoding='utf-8') as f:
                        file_patterns = f.readlines()
                    patterns.extend([
                        p.strip() for p in file_patterns
                        if p.strip() and not p.startswith('#')
                    ])
                except Exception:
                    continue
                    
        return patterns
