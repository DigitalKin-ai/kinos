import os
import subprocess
from utils.logger import Logger
from pathlib import Path

class AiderManager:
    """Manager class for handling aider operations."""
    
    def __init__(self):
        """Initialize the manager with logger."""
        self.logger = Logger()

    def run_aider(self, objective_filepath, map_filepath, agent_filepath):
        """
        Execute aider operation with defined context.
        
        Args:
            objective_filepath (str): Path to objective file
            map_filepath (str): Path to context map file
            agent_filepath (str): Path to agent configuration file
            
        Raises:
            ValueError: If required files are invalid
            subprocess.CalledProcessError: If aider execution fails
        """
        try:
            self.logger.info("Starting aider operation")
            
            # Validate input files
            if not self._validate_files(objective_filepath, map_filepath, agent_filepath):
                raise ValueError("Invalid or missing input files")
                
            # Load context map
            context_files = self._load_context_map(map_filepath)
            
            # Configure aider command
            cmd = self._build_aider_command(
                objective_filepath,
                agent_filepath,
                context_files
            )
            
            # Execute aider
            self._execute_aider(cmd)
            
            self.logger.info("Aider operation completed successfully")
            
        except Exception as e:
            self.logger.error(f"Aider operation failed: {str(e)}")
            raise

    def _validate_files(self, *filepaths):
        """Validate all input files exist and are readable."""
        for filepath in filepaths:
            if not filepath or not os.path.exists(filepath):
                self.logger.error(f"Missing file: {filepath}")
                return False
            if not os.path.isfile(filepath) or not os.access(filepath, os.R_OK):
                self.logger.error(f"Cannot read file: {filepath}")
                return False
        return True

    def _load_context_map(self, map_filepath):
        """
        Load and parse context map file.
        
        Returns:
            list: List of context file paths
        """
        try:
            context_files = []
            with open(map_filepath, 'r') as f:
                for line in f:
                    if line.strip().startswith('- '):
                        filepath = line.strip()[2:]
                        if os.path.exists(filepath):
                            context_files.append(filepath)
                        else:
                            self.logger.warning(f"Context file not found: {filepath}")
            return context_files
            
        except Exception as e:
            self.logger.error(f"Error loading context map: {str(e)}")
            raise

    def _build_aider_command(self, objective_filepath, agent_filepath, context_files):
        """
        Build aider command with all required arguments.
        
        Returns:
            list: Command arguments for subprocess
        """
        cmd = ["python", "-m", "aider"]
        
        # Add required aider arguments
        cmd.extend([
            "--model", "gpt-4o-mini",
            "--edit-format", "diff", 
            "--yes-always",
            "--cache-prompts",
            "--no-pretty"
        ])
        
        # Add context files
        cmd.extend(context_files)
        
        # Add agent prompt as read-only
        cmd.extend(['--read', agent_filepath])
        
        # Add objective as initial prompt
        with open(objective_filepath, 'r') as f:
            objective = f.read()
            cmd.extend(['--message', objective])
            
        return cmd

    def _parse_commit_type(self, commit_msg):
        """
        Parse commit message to determine type and corresponding emoji.
        
        Returns:
            tuple: (type, emoji)
        """
        commit_types = {
            'feat': '✨',
            'fix': '🐛', 
            'docs': '📚',
            'style': '💎',
            'refactor': '♻️',
            'perf': '⚡️',
            'test': '🧪',
            'build': '📦',
            'ci': '🔄',
            'chore': '🔧',
            'revert': '⏪'
        }
        
        # Check if commit message starts with any known type
        for commit_type, emoji in commit_types.items():
            if commit_msg.lower().startswith(f"{commit_type}:"):
                return commit_type, emoji
                
        # Default to other
        return "other", "🔨"

    def _execute_aider(self, cmd):
        """Execute aider command and handle results."""
        try:
            self.logger.info(f"Executing aider command: {' '.join(cmd)}")
            
            # Run aider with configured command
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Parse output for commits
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if line.startswith("Commit: "):
                    commit_msg = line[8:].strip()  # Remove "Commit: " prefix
                    
                    # Extract agent name from command
                    agent_filepath = [arg for arg in cmd if arg.endswith('.md') and '.agent.' in arg][0]
                    agent_name = os.path.basename(agent_filepath).replace('.aider.agent.', '').replace('.md', '')
                    
                    # Parse commit type and get emoji
                    commit_type, emoji = self._parse_commit_type(commit_msg)
                    
                    # Log formatted commit message
                    self.logger.info(f"Agent {agent_name} made {commit_type} commit {emoji}: {commit_msg}")
            
            # Log other output
            if result.stderr:
                self.logger.warning(f"Aider warnings:\n{result.stderr}")
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Aider execution failed: {str(e)}")
            if e.output:
                self.logger.error(f"Error output:\n{e.output}")
            raise
