"""
AiderCommandBuilder - Handles Aider command construction and execution
"""
import os
import subprocess
from typing import List, Dict, Any
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

class AiderCommandBuilder:
    """Builds and executes Aider commands"""
    
    def __init__(self, agent_name: str):
        """Initialize with agent name"""
        self.agent_name = agent_name

    def get_model_args(self) -> List[str]:
        """Get model-specific command arguments"""
        return [
            "--model", "claude-3-5-haiku-20241022",
            "--yes-always",
            "--cache-prompts",
            "--no-pretty",
            "--architect"
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
        for file in files:
            # Skip ignored files
            if any(pattern in file for pattern in ignore_patterns):
                continue
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

    def build_command(self, prompt: str, files: List[str]) -> List[str]:
        """
        Build Aider command with arguments
        
        Args:
            prompt: Prompt to send to Aider
            files: List of files to include
            
        Returns:
            List of command arguments
        """
        cmd = ["python", "-m", "aider"]
        
        # Add the PYTHONPATH environment variable when executing
        # to ensure your modified aider version is found
        os.environ["PYTHONPATH"] = os.path.join(os.environ.get("PYTHONPATH", ""), 
                                            r"C:\Users\conta\parallagon")
        
        cmd.extend(self.get_model_args())
        cmd.extend(self.get_file_args(files, self.get_ignore_patterns(os.getcwd())))
        
        # Use the agent name from initialization
        cmd.extend(["--chat-history-file", f".aider.{self.agent_name}.chat.history.md"])
        cmd.extend(["--input-history-file", f".aider.{self.agent_name}.input.history.md"])
        
        cmd.extend(["--message", prompt])
        
        if not self.validate_command(cmd):
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
