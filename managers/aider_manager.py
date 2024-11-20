import os
import time
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
        Creates empty files if they don't exist.
        
        Returns:
            list: List of context file paths
        """
        try:
            context_files = []
            with open(map_filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('- '):
                        filepath = line.strip()[2:]
                        if not os.path.exists(filepath):
                            # Create directory structure if needed
                            os.makedirs(os.path.dirname(filepath), exist_ok=True)
                            # Create empty file
                            with open(filepath, 'w', encoding='utf-8') as new_file:
                                pass
                            self.logger.info(f"📄 Created empty file: {filepath}")
                        context_files.append(filepath)
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
            
        # Add global map as read-only
        cmd.extend(['--read', 'map.md'])

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

    def _handle_post_aider(self, agent_name, before_state, after_state, phase_name):
        """Handle all post-aider operations for a single phase."""
        modified_files = self._get_modified_files(before_state, after_state)
        if modified_files:
            self.logger.info(f"📝 Agent {agent_name} {phase_name} phase modified {len(modified_files)} files")
            map_manager = MapManager()
            for file_path in modified_files:
                try:
                    file_path = file_path.encode('latin1').decode('utf-8')
                    self.logger.info(f"🔄 Agent {agent_name} updating global map for: {file_path}")
                    map_manager.update_global_map(file_path)
                    self.logger.debug(f"✅ Agent {agent_name} successfully updated map for: {file_path}")
                except Exception as e:
                    self.logger.error(f"❌ Agent {agent_name} failed to update map for {file_path}: {str(e)}")
        return modified_files

    def _run_aider_phase(self, cmd, agent_name, phase_name, phase_prompt):
        """Run a single aider phase and handle its results."""
        phase_start = time.time()
        self.logger.info(f"{phase_name} Agent {agent_name} starting phase at {phase_start}")
        
        # Prepare command with phase-specific prompt
        phase_cmd = cmd.copy()
        phase_cmd[-1] = phase_cmd[-1] + f"\n{phase_prompt}"
        
        # Get initial state
        initial_state = self._get_git_file_states()
        
        # Execute aider
        process = subprocess.Popen(
            phase_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace'
        )
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            self.logger.error(f"{phase_name} process failed with return code {process.returncode}")
            raise subprocess.CalledProcessError(process.returncode, phase_cmd, stdout, stderr)

        # Get final state and handle post-aider operations
        final_state = self._get_git_file_states()
        modified_files = self._handle_post_aider(agent_name, initial_state, final_state, phase_name)
        
        phase_end = time.time()
        self.logger.info(f"✨ Agent {agent_name} completed {phase_name} phase in {phase_end - phase_start:.2f} seconds")
        
        return modified_files, final_state

    def _execute_aider(self, cmd):
        """Execute aider command and handle results."""
        try:
            # Extract agent name from cmd arguments
            agent_name = None
            for i, arg in enumerate(cmd):
                if "--chat-history-file" in arg and i+1 < len(cmd):
                    agent_name = cmd[i+1].replace('.aider.history.', '').replace('.md', '')
                    break

            # Log start time
            start_time = time.time()
            self.logger.info(f"⏳ Agent {agent_name} starting aider execution at {start_time}")

            # Run production phase
            production_files, production_state = self._run_aider_phase(
                cmd, agent_name, "🏭 Production", 
                "Focus on the Production Objective"
            )

            # Run role-specific phase
            role_files, role_state = self._run_aider_phase(
                cmd, agent_name, "👤 Role-specific",
                "Focus on the Role-specific Objective"
            )

            # Run final check phase
            final_files, final_state = self._run_aider_phase(
                cmd, agent_name, "🔍 Final Check",
                "--> Any additional changes required?"
            )

            # Log total duration and summary
            total_duration = time.time() - start_time
            self.logger.info(f"🎯 Agent {agent_name} completed total aider execution in {total_duration:.2f} seconds")
            
            # Combine all modified files
            all_modified = set()
            all_modified.update(production_files or [])
            all_modified.update(role_files or [])
            all_modified.update(final_files or [])
            
            if all_modified:
                self.logger.info(f"📝 Agent {agent_name} modified total of {len(all_modified)} files")

        except Exception as e:
            agent_msg = f"Agent {agent_name} " if agent_name else ""
            self.logger.error(f"💥 {agent_msg}aider execution failed: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            if hasattr(e, 'output'):
                self.logger.error(f"Error output:\n{e.output}")
            raise
