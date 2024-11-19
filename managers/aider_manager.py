import os
import subprocess
from utils.logger import Logger
from pathlib import Path
from managers.map_manager import MapManager

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
            with open(map_filepath, 'r', encoding='utf-8') as f:
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
        with open(objective_filepath, 'r', encoding='utf-8') as f:
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

    def _get_modified_files(self, aider_output):
        """Extract modified file paths from aider output."""
        modified_files = set()
        current_file = None
        in_search_block = False
        
        # Process aider output line by line
        for line in aider_output.split('\n'):
            line = line.strip()
            
            # If we find a SEARCH marker, the previous non-empty line should be the filepath
            if line.startswith('<<<<<<< SEARCH'):
                in_search_block = True
                if current_file:  # We found a filepath in the previous line
                    if os.path.exists(current_file):
                        modified_files.add(current_file)
                        self.logger.debug(f"✅ Added file from SEARCH block: {current_file}")
            # Store potential filepath
            elif line and not in_search_block and not line.startswith('=======') and not line.startswith('>>>>>>>'):
                current_file = line
            # Reset search block flag at the end of the block
            elif line.startswith('>>>>>>> REPLACE'):
                in_search_block = False
                current_file = None
                        
        return list(modified_files)

    def _execute_aider(self, cmd):
        """Execute aider command and handle results."""
        try:
            self.logger.debug(f"🤖 Starting aider execution with command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='replace'
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"Aider process failed with return code {process.returncode}")
                raise subprocess.CalledProcessError(process.returncode, cmd, stdout, stderr)
                
            self.logger.debug("Processing aider output for commits and file changes...")
            
            # Combine output safely
            all_output = (stdout or "") + "\n" + (stderr or "")
            
            # Track current commit's modified files
            current_commit_files = set()
            current_file = None
            in_search_block = False
            commit_count = 0
            
            for line in all_output.split('\n'):
                line = line.strip()
                
                # Log the raw line for debugging
                self.logger.debug(f"RAW LINE: {line}")
                
                # If we find a SEARCH marker, the previous non-empty line should be the filepath
                if line.startswith('<<<<<<< SEARCH'):
                    in_search_block = True
                    if current_file:  # We found a filepath in the previous line
                        self.logger.debug(f"🔍 Found file in SEARCH block: {current_file}")
                        if os.path.exists(current_file):
                            current_commit_files.add(current_file)
                            self.logger.debug(f"✅ File exists: {current_file}")
                        else:
                            self.logger.debug(f"❌ File not found: {current_file}")
                # Store potential filepath
                elif line and not in_search_block and not line.startswith('=======') and not line.startswith('>>>>>>>'):
                    current_file = line
                    self.logger.debug(f"🔍 Potential file path found: {current_file}")
                # Reset search block flag at the end of the block
                elif line.startswith('>>>>>>> REPLACE'):
                    in_search_block = False
                    current_file = None
                            
                # End of diff section / Commit line
                elif line.startswith('commit ') or line.startswith('Commit '):
                    commit_count += 1
                    
                    self.logger.debug(f"💾 Processing commit #{commit_count}")
                    self.logger.debug(f"📄 Modified files for this commit: {current_commit_files}")
                    
                    try:
                        # Parse commit info
                        if line.startswith('Commit '):
                            commit_parts = line.split("Commit ")[1]
                        else:
                            commit_parts = line.split("commit ")[1]
                            
                        commit_hash = commit_parts.split()[0][:7]
                        commit_msg = " ".join(commit_parts.split()[1:])
                        
                        # Extract agent name
                        agent_filepath = [arg for arg in cmd if arg.endswith('.md') and '.agent.' in arg][0]
                        agent_name = os.path.basename(agent_filepath).replace('.aider.agent.', '').replace('.md', '')
                        
                        # Parse commit type
                        commit_type, emoji = self._parse_commit_type(commit_msg)
                        
                        self.logger.success(f"Agent {agent_name} made {commit_type} commit {emoji} ({commit_hash}): {commit_msg}")
                        
                        # Update map for modified files
                        if current_commit_files:
                            map_manager = MapManager()
                            for modified_file in current_commit_files:
                                try:
                                    self.logger.info(f"🔄 Updating global map for: {modified_file}")
                                    map_manager.update_global_map(modified_file)
                                    self.logger.debug(f"✅ Successfully updated map for: {modified_file}")
                                except Exception as map_error:
                                    self.logger.error(f"❌ Failed to update map for {modified_file}: {str(map_error)}")
                                    self.logger.error(f"Error details: {type(map_error).__name__}: {str(map_error)}")
                            
                            # Clear for next commit
                            current_commit_files.clear()
                            
                    except Exception as parse_error:
                        self.logger.error(f"Failed to parse commit line: {line}")
                        self.logger.error(f"Parse error details: {type(parse_error).__name__}: {str(parse_error)}")
                        continue
            
            self.logger.debug(f"Processed {commit_count} commits total")
            
            # Handle remaining files
            if current_commit_files:
                self.logger.debug(f"Processing {len(current_commit_files)} remaining modified files")
                map_manager = MapManager()
                for modified_file in current_commit_files:
                    try:
                        self.logger.info(f"🔄 Updating global map for remaining file: {modified_file}")
                        map_manager.update_global_map(modified_file)
                        self.logger.debug(f"✅ Successfully updated map for remaining file: {modified_file}")
                    except Exception as map_error:
                        self.logger.error(f"❌ Failed to update remaining file {modified_file}: {str(map_error)}")
                        self.logger.error(f"Error details: {type(map_error).__name__}: {str(map_error)}")
                        
        except Exception as e:
            self.logger.error(f"💥 Aider execution failed: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            if hasattr(e, 'output'):
                self.logger.error(f"Error output:\n{e.output}")
            raise
