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
            self.logger.info("🚀 Starting aider operation")
            
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
            
            self.logger.info("✅ Aider operation completed successfully")
            
        except Exception as e:
            self.logger.error(f"Aider operation failed: {str(e)}")
            raise

    def _validate_files(self, *filepaths):
        """Validate all input files exist and are readable."""
        for filepath in filepaths:
            if not filepath or not os.path.exists(filepath):
                self.logger.error(f"❌ Missing file: {filepath}")
                return False
            if not os.path.isfile(filepath) or not os.access(filepath, os.R_OK):
                self.logger.error(f"🚫 Cannot read file: {filepath}")
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
                            self.logger.warning(f"⚠️ Context file not found: {filepath}")
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
        # Extract agent name from filepath for history files
        agent_name = os.path.basename(agent_filepath).replace('.aider.agent.', '').replace('.md', '')
        
        cmd = ["python", "-m", "aider"]
        
        # Add required aider arguments
        cmd.extend([
            "--model", "gpt-4o-mini",
            "--edit-format", "diff", 
            "--yes-always",
            "--cache-prompts",
            "--no-pretty",
            "--chat-history-file", f".aider.history.{agent_name}.md",
            "--input-history-file", f".aider.input.{agent_name}.md"
        ])
        
        # Add context files with --file prefix
        for context_file in context_files:
            cmd.extend(['--file', context_file])
            
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
            # Core Changes
            'feat': '✨',
            'fix': '🐛',
            'refactor': '♻️',
            'perf': '⚡️',
            
            # Documentation & Style
            'docs': '📚',
            'style': '💎',
            'ui': '🎨',
            'content': '📝',
            
            # Testing & Quality
            'test': '🧪',
            'qual': '✅',
            'lint': '🔍',
            'bench': '📊',
            
            # Infrastructure
            'build': '📦',
            'ci': '🔄',
            'deploy': '🚀',
            'env': '🌍',
            'config': '⚙️',
            
            # Maintenance
            'chore': '🔧',
            'clean': '🧹',
            'deps': '📎',
            'revert': '⏪',
            
            # Security & Data
            'security': '🔒',
            'auth': '🔑',
            'data': '💾',
            'backup': '💿',
            
            # Project Management
            'init': '🎉',
            'release': '📈',
            'break': '💥',
            'merge': '🔀',
            
            # Special Types
            'wip': '🚧',
            'hotfix': '🚑',
            'arch': '🏗️',
            'api': '🔌',
            'i18n': '🌐'
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
            # Log command as debug
            self.logger.debug(f"🤖 Executing aider command: {' '.join(cmd)}")
            
            # Run aider with configured command
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Log raw output as debug
            if result.stdout:
                self.logger.debug(f"📝 Aider stdout:\n{result.stdout}")
            
            # Parse both stdout and stderr for commits
            all_output = result.stdout + "\n" + result.stderr
            output_lines = all_output.split('\n')
            
            # Look for commit lines - they start with "Commit" followed by a hash
            for line in output_lines:
                line = line.strip()
                if "Commit " in line:  # More lenient check for commit messages
                    try:
                        # Split on "Commit " to get everything after it
                        commit_parts = line.split("Commit ")[1]
                        # First word is the hash
                        commit_hash = commit_parts.split()[0][:7]
                        # Everything after the hash is the message
                        commit_msg = " ".join(commit_parts.split()[1:])
                        
                        # Extract agent name from command
                        agent_filepath = [arg for arg in cmd if arg.endswith('.md') and '.agent.' in arg][0]
                        agent_name = os.path.basename(agent_filepath).replace('.aider.agent.', '').replace('.md', '')
                        
                        # Parse commit type and get emoji
                        commit_type, emoji = self._parse_commit_type(commit_msg)
                        
                        # Log formatted commit message as success - now with full message
                        self.logger.info(f"Agent {agent_name} made {commit_type} commit {emoji} ({commit_hash}): {commit_msg}")
                    except Exception as parse_error:
                        self.logger.debug(f"Failed to parse commit line: {line}")
                        continue
            
            # Log stderr as debug if present, warning if contains error
            if result.stderr:
                if "error" in result.stderr.lower():
                    self.logger.warning(f"⚠️ Aider warnings:\n{result.stderr}")
                else:
                    self.logger.debug(f"📝 Aider stderr:\n{result.stderr}")
                    
        except subprocess.CalledProcessError as e:
            self.logger.error(f"💥 Aider execution failed: {str(e)}")
            if e.output:
                self.logger.error(f"Error output:\n{e.output}")
            raise
