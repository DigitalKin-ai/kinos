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
            "--restore-chat-history",
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
        try:
            # Decode commit message if it's bytes
            if isinstance(commit_msg, bytes):
                commit_msg = commit_msg.decode('utf-8')
                
            # Fix potential encoding issues
            commit_msg = commit_msg.encode('latin1').decode('utf-8')
            
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
            
        except UnicodeError as e:
            self.logger.warning(f"⚠️ Encoding issue with commit message: {str(e)}")
            return "other", "🔨"

    def _get_git_file_states(self):
        """Get dictionary of tracked files and their current hash."""
        try:
            # Get list of tracked files with their hashes
            result = subprocess.run(
                ['git', 'ls-files', '-s'],
                capture_output=True,
                text=True,
                check=True
            )
            
            file_states = {}
            for line in result.stdout.splitlines():
                # Format: <mode> <hash> <stage> <file>
                parts = line.split()
                if len(parts) >= 4:
                    file_path = ' '.join(parts[3:])  # Handle filenames with spaces
                    file_hash = parts[1]
                    file_states[file_path] = file_hash
                    
            return file_states
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get git file states: {str(e)}")
            raise

    def _get_modified_files(self, before_state, after_state):
        """Compare before and after states to find modified files."""
        modified_files = []
        
        # Check for modified files
        for file_path, after_hash in after_state.items():
            before_hash = before_state.get(file_path)
            if before_hash != after_hash:
                modified_files.append(file_path)
                self.logger.debug(f"🔍 Detected change in {file_path}")
                self.logger.debug(f"  Before hash: {before_hash}")
                self.logger.debug(f"  After hash: {after_hash}")
                self.logger.debug(f"📝 Modified file: {file_path}")
        
        return modified_files

    def _execute_aider(self, cmd):
        """Execute aider command and handle results."""
        try:
            # Extract agent name from cmd arguments
            agent_filepath = None
            for i, arg in enumerate(cmd):
                if arg == '--read' and i + 1 < len(cmd):
                    agent_filepath = cmd[i + 1]
                    break
            
            agent_name = "unknown"
            if agent_filepath:
                agent_name = os.path.basename(agent_filepath).replace('.aider.agent.', '').replace('.md', '')

            # Get list of tracked files and their hashes before any aider runs
            initial_state = self._get_git_file_states()

            # First call - Production objective
            production_cmd = cmd.copy()
            production_cmd[-1] = production_cmd[-1] + "\nFocus on the production objective"
            self.logger.info(f"🏭 Executing production-focused aider operation for {agent_name} agent...")
            
            # Execute first aider call with timeout
            process = subprocess.run(
                production_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='replace',
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
                timeout=300  # 5 minute timeout
            )

            if process.returncode != 0:
                self.logger.error(f"Production aider process failed with return code {process.returncode}")
                raise subprocess.CalledProcessError(process.returncode, production_cmd, process.stdout, process.stderr)

        except subprocess.TimeoutExpired:
            self.logger.error("Production aider process timed out")
            raise

            # Get intermediate state after first call
            intermediate_state = self._get_git_file_states()

            # Second call - Role-specific objective
            role_cmd = cmd.copy()
            role_cmd[-1] = role_cmd[-1] + "\nFocus on the role-specific objective"
            self.logger.info(f"👤 Executing {agent_name}-specific aider operation...")
            
            # Execute second aider call with timeout
            process = subprocess.run(
                role_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='replace',
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
                timeout=300  # 5 minute timeout
            )

            if process.returncode != 0:
                self.logger.error(f"Role-specific aider process failed with return code {process.returncode}")
                raise subprocess.CalledProcessError(process.returncode, role_cmd, process.stdout, process.stderr)

        except subprocess.TimeoutExpired:
            self.logger.error("Role-specific aider process timed out")
            raise

            # Get final state after both calls
            final_state = self._get_git_file_states()

            # Find all modified files across both operations
            modified_files = set()
            
            # Check for files modified in first operation
            production_modified = self._get_modified_files(initial_state, intermediate_state)
            if production_modified:
                self.logger.info(f"📝 Production phase modified {len(production_modified)} files")
                modified_files.update(production_modified)
                
            # Check for files modified in second operation
            role_modified = self._get_modified_files(intermediate_state, final_state)
            if role_modified:
                self.logger.info(f"📝 Role-specific phase modified {len(role_modified)} files")
                modified_files.update(role_modified)

            # Update global map for all modified files
            if modified_files:
                self.logger.info(f"📝 Total of {len(modified_files)} modified files")
                map_manager = MapManager()
                for file_path in modified_files:
                    try:
                        # Ensure file path is properly encoded
                        file_path = file_path.encode('latin1').decode('utf-8')
                        self.logger.info(f"🔄 Updating global map for: {file_path}")
                        map_manager.update_global_map(file_path)
                        self.logger.debug(f"✅ Successfully updated map for: {file_path}")
                    except Exception as e:
                        self.logger.error(f"❌ Failed to update map for {file_path}: {str(e)}")

        except Exception as e:
            self.logger.error(f"💥 Aider execution failed: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            if hasattr(e, 'output'):
                self.logger.error(f"Error output:\n{e.output}")
            raise
