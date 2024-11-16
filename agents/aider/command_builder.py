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
        args = []
        
        # Filter ignored files first
        valid_files = [
            file for file in files 
            if not any(pattern in file for pattern in ignore_patterns)
        ]
        
        # Define read-only files
        readonly_files = ["demande.md", "map.md"]
        
        # Get agent's prompt file path using team_types directory
        from utils.path_manager import PathManager
        kinos_root = PathManager.get_kinos_root()
        team_types_dir = os.path.join(kinos_root, "team_types")
        
        # Find team directory containing the prompt
        prompt_path = None
        
        # Get team service to find the correct team
        from services import init_services
        services = init_services(None)
        team_service = services['team_service']
        
        for team in team_service.team_types:
            if self.agent_name in team_service.get_team_agents(team['id']):
                possible_path = os.path.join(team_types_dir, team['id'], f"{self.agent_name}.md")
                if os.path.exists(possible_path):
                    prompt_path = possible_path
                    break
        
        # Remove readonly files from valid_files if present to avoid duplicates
        valid_files = [f for f in valid_files if f not in readonly_files]
        
        # Limit remaining files to 10 random if needed
        if len(valid_files) > 10:
            import random
            valid_files = random.sample(valid_files, 10)
        
        # Add read-only files first with --read flag
        for file in readonly_files:
            args.extend(["--read", file])
            
        # Add agent prompt as read-only if found
        if prompt_path:
            args.extend(["--read", prompt_path])
            
        # Add key files that should be editable
        key_files = ["todolist.md", "directives.md"]
        for file in key_files:
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
        """
        Build Aider command with arguments
        
        Args:
            instructions: ModelRouter-generated instructions to send to Aider
            files: List of files to include
            
        Returns:
            List of command arguments
        """
        cmd = ["python", "-m", "aider"]
        
        # Add the PYTHONPATH environment variable when executing
        os.environ["PYTHONPATH"] = os.path.join(os.environ.get("PYTHONPATH", ""), 
                                        r"C:\Users\conta\parallagon")
        
        cmd.extend(self.get_model_args())
        cmd.extend(self.get_file_args(files, self.get_ignore_patterns(os.getcwd())))
        
        # Use team_types directory
        team_types_dir = os.path.join(PathManager.get_kinos_root(), "team_types")
        
        # Get team ID from agent name using team service
        from services import init_services
        services = init_services(None)
        team_service = services['team_service']
        
        team_id = None
        for team in team_service.team_types:
            if self.agent_name in team_service.get_team_agents(team['id']):
                team_id = team['id']
                break
        
        if team_id:
            # Use team_types directory for history files
            history_path = os.path.join(team_types_dir, team_id)
        else:
            # Fallback to current directory if team not found
            history_path = os.getcwd()
            
        # Use the correct paths for history files
        cmd.extend([
            "--chat-history-file", 
            os.path.join(history_path, f".kinos.{self.agent_name}.chat.history.md")
        ])
        cmd.extend([
            "--input-history-file", 
            os.path.join(history_path, f".kinos.{self.agent_name}.input.history.md")
        ])
        
        # Stringify the instructions with robust escaping
        stringified_instructions = instructions.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        cmd.extend(["--message", f'"{stringified_instructions} ALWAYS DIRECTLY PROCEED WITH THE MODIFICATIONS, USING THE SEARCH/REPLACE FORMAT."'])
        
        if not self.validate_command(cmd):
            self.logger.log(f"Invalid command configuration for {self.agent_name}", 'error')
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
