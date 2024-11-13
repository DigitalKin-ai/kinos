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
    
    def build_command(self, prompt: str, files: List[str]) -> List[str]:
        """
        Build Aider command with arguments
        
        Args:
            prompt: Prompt to send to Aider
            files: List of files to include
            
        Returns:
            List of command arguments
        """
        cmd = [
            "aider",
            "--model", "claude-3-5-haiku-20241022",
            "--yes-always",
            "--cache-prompts",
            "--no-pretty",
            "--architect"
        ]
        
        # Add files
        for file in files:
            cmd.extend(["--file", file])
            
        # Add prompt
        cmd.extend(["--message", prompt])
        
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
