import os
import time
import json
import subprocess
from utils.logger import Logger
from utils.fs_utils import FSUtils
from pathlib import Path
from managers.vision_manager import VisionManager

class AiderManager:
    """Manager class for handling aider operations."""
    
    def __init__(self):
        """Initialize the manager with logger."""
        self.logger = Logger()
        self._vision_manager = VisionManager()

    def _validate_repo_visualizer(self):
        """
        Validate that repo-visualizer is properly installed and configured.
        
        Raises:
            FileNotFoundError: If required files are missing
            ValueError: If configuration is invalid
        """
        repo_visualizer_path = self._get_repo_visualizer_path()
        dist_path = os.path.join(repo_visualizer_path, 'dist')
        index_js = os.path.join(dist_path, 'index.js')
        
        if not os.path.exists(repo_visualizer_path):
            raise FileNotFoundError(
                f"repo-visualizer not found at {repo_visualizer_path}. "
                "Please install it first."
            )
            
        if not os.path.exists(index_js):
            raise FileNotFoundError(
                f"repo-visualizer build not found at {index_js}. "
                "Please build repo-visualizer first."
            )
            
        if not os.access(index_js, os.X_OK):
            raise ValueError(
                f"repo-visualizer build at {index_js} is not executable. "
                "Please check file permissions."
            )

    async def run_aider(self, objective_filepath, map_filepath, agent_filepath, model="gpt-4o-mini"):
        """
        Execute aider operation with defined context.
        
        Args:
            objective_filepath (str): Path to objective file
            map_filepath (str): Path to context map file
            agent_filepath (str): Path to agent configuration file
            model (str): Model name to use (default: gpt-4o-mini)
            
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
            
            # Get agent name from filepath for post-processing
            agent_name = os.path.basename(agent_filepath).replace('.aider.agent.', '').replace('.md', '')
            
            # Get initial git state
            before_state = self._get_git_file_states()
            self.logger.debug(f"📝 Captured initial git state with {len(before_state)} files")
            
            # Configure aider command
            cmd = self._build_aider_command(
                objective_filepath,
                map_filepath,
                agent_filepath,
                context_files,
                model=model
            )
            
            # Execute aider with await
            await self._execute_aider(cmd)
            
            # Get final git state
            after_state = self._get_git_file_states()
            self.logger.debug(f"📝 Captured final git state with {len(after_state)} files")
            
            # Get latest commit info
            try:
                result = subprocess.run(
                    ['git', 'log', '-1', '--pretty=format:%h - %s'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if result.stdout:
                    self.logger.success(f"🔨 Git commit: {result.stdout}")
            except subprocess.CalledProcessError as e:
                self.logger.warning(f"Could not get commit info: {e}")
            
            # Handle post-aider operations
            await self._handle_post_aider(agent_name, before_state, after_state, "Production")
            
            self.logger.info("✅ Aider operation completed successfully")
            
        except Exception as e:
            self.logger.error(f"Aider operation failed: {str(e)}")
            raise
            
    def fix_git_encoding(self):
        """Fix encoding of existing git commits."""
        try:
            # Get all commits
            result = subprocess.run(
                ['git', 'log', '--format=%H'],
                capture_output=True,
                text=True,
                check=True
            )
            commit_hashes = result.stdout.splitlines()
            
            for commit_hash in commit_hashes:
                # Get commit message
                result = subprocess.run(
                    ['git', 'log', '-1', '--pretty=%B', commit_hash],
                    capture_output=True,
                    text=True,
                    check=True
                )
                commit_msg = result.stdout
                
                # Fix encoding
                try:
                    fixed_msg = commit_msg.encode('latin1').decode('utf-8')
                    
                    # Amend commit with fixed message
                    subprocess.run(
                        ['git', 'filter-branch', '-f', '--msg-filter', 
                         f'echo "{fixed_msg}"', f'{commit_hash}^..{commit_hash}'],
                        check=True
                    )
                    
                except UnicodeError as e:
                    self.logger.warning(f"⚠️ Could not fix encoding for commit {commit_hash}: {str(e)}")
                    continue
                    
            self.logger.success("✨ Git commit encodings fixed")
            
        except Exception as e:
            self.logger.error(f"Failed to fix git encodings: {str(e)}")
            raise

    def _validate_mission_file(self, mission_filepath):
        """Validate that the mission file exists and is readable.
        
        Args:
            mission_filepath (str): Path to mission file
            
        Returns:
            bool: True if file is valid, False otherwise
            
        Side Effects:
            Logs error messages if validation fails
        """
        if not os.path.exists(mission_filepath):
            self.logger.error("❌ Mission file not found!")
            self.logger.info("\n📋 To start KinOS, you must:")
            self.logger.info("   1. Either create a '.aider.mission.md' file in the current folder")
            self.logger.info("   2. Or specify the path to your mission file with --mission")
            self.logger.info("\n💡 Examples:")
            self.logger.info("   kin run agents --generate")
            self.logger.info("   kin run agents --generate --mission path/to/my_mission.md")
            self.logger.info("\n📝 The mission file must contain your project description.")
            return False
        
        if not os.access(mission_filepath, os.R_OK):
            self.logger.error(f"❌ Cannot read mission file: {mission_filepath}")
            return False
            
        return True

    def _validate_mission_file(self, mission_filepath):
        """
        Validate that mission file exists and is readable.
        
        Args:
            mission_filepath (str): Path to mission file
            
        Returns:
            bool: True if file is valid, False otherwise
            
        Side Effects:
            Logs error messages if validation fails
        """
        if not os.path.exists(mission_filepath):
            self.logger.error("❌ Mission file not found!")
            self.logger.info("\n📋 To start KinOS, you must:")
            self.logger.info("   1. Either create a '.aider.mission.md' file in the current folder")
            self.logger.info("   2. Or specify the path to your mission file with --mission")
            self.logger.info("\n💡 Examples:")
            self.logger.info("   kin run agents --generate")
            self.logger.info("   kin run agents --generate --mission path/to/my_mission.md")
            self.logger.info("\n📝 The mission file must contain your project description.")
            return False
        
        if not os.access(mission_filepath, os.R_OK):
            self.logger.error(f"❌ Cannot read mission file: {mission_filepath}")
            return False
            
        return True

    def _validate_files(self, *filepaths):
        """Validate that all input files exist and are readable.
        
        Args:
            *filepaths: Variable number of file paths to validate
            
        Returns:
            bool: True if all files are valid, False otherwise
        """
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

    def _build_aider_command(self, objective_filepath, map_filepath, agent_filepath, context_files, model="gpt-4o-mini"):
        """
        Build aider command with all required arguments.
        
        Args:
            objective_filepath (str): Path to objective file
            map_filepath (str): Path to map file
            agent_filepath (str): Path to agent file
            context_files (list): List of context files
            model (str): Model name to use (default: gpt-4o-mini)
            
        Returns:
            list: Command arguments for subprocess
        """
        # Extract agent name from filepath for history files
        agent_name = os.path.basename(agent_filepath).replace('.aider.agent.', '').replace('.md', '')
        
        cmd = ["python", "-m", "aider"]
        
        # Add required aider arguments
        cmd.extend([
            "--model", model,
            "--edit-format", "diff", 
            "--yes-always",
            "--no-pretty",
            "--no-fancy-input",
            "--encoding", "utf-8",  # Force UTF-8 encoding
            "--chat-history-file", f".aider.history.{agent_name}.md",
            "--restore-chat-history",
            "--input-history-file", f".aider.input.{agent_name}.md"
        ])
        
        # Add context files with --file prefix
        for context_file in context_files:
            cmd.extend(['--file', context_file])
            
        # Add global map as read-only
        cmd.extend(['--file', 'todolist.md'])
        #cmd.extend(['--read', 'map.md'])

        # Add agent prompt as read-only
        cmd.extend(['--read', agent_filepath])
        
        # Combine objective and map content
        combined_message = ""
        
        # Add objective content
        with open(objective_filepath, 'r', encoding='utf-8') as f:
            objective_content = f.read()
            combined_message += "# Objective\n" + objective_content + "\n\n"
        
        # Add map content
        with open(map_filepath, 'r', encoding='utf-8') as f:
            map_content = f.read()
            combined_message += "# Context Map\n" + map_content
            
        # Add combined message as initial prompt
        cmd.extend(['--message', combined_message])
            
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

    async def _handle_post_aider(self, agent_name, before_state, after_state, phase_name):
        """Handle all post-aider operations for a single phase."""
        modified_files = self._get_modified_files(before_state, after_state)
        if modified_files:
            self.logger.info(f"📝 Agent {agent_name} {phase_name} phase modified {len(modified_files)} files")
            
            # Track if any files were created or deleted
            files_changed = False
            for file_path in modified_files:
                try:
                    file_path = file_path.encode('latin1').decode('utf-8')
                    # Check if file was created or deleted
                    if file_path not in before_state or file_path not in after_state:
                        files_changed = True
                        
                except Exception as e:
                    self.logger.error(f"❌ Agent {agent_name} failed to process {file_path}: {str(e)}")
            
            # Generate new visualization if files were created or deleted
            if files_changed:
                try:
                    self.logger.info("🎨 Updating repository visualization...")
                    await self._vision_manager.generate_visualization()
                    self.logger.success("✨ Repository visualization updated")
                except Exception as e:
                    self.logger.error(f"❌ Failed to update visualization: {str(e)}")
                    
        return modified_files

    async def _run_aider_phase(self, cmd, agent_name, phase_name, phase_prompt):
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
        modified_files = await self._handle_post_aider(agent_name, initial_state, final_state, phase_name)
    
        # Get latest commit info if files were modified
        if modified_files:
            try:
                result = subprocess.run(
                    ['git', 'log', '-1', '--pretty=format:%h - %s'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if result.stdout:
                    self.logger.success(f"🔨 Git commit: {result.stdout}")
            except subprocess.CalledProcessError as e:
                self.logger.warning(f"Could not get commit info: {e}")

            # Push changes to GitHub
            try:
                self.logger.info(f"🔄 Attempting to push changes...")
                subprocess.run(['git', 'push'], check=True, capture_output=True, text=True)
                self.logger.info(f"✨ Changes pushed successfully")
            except subprocess.CalledProcessError as e:
                # Just log info for push failures since remote might not be configured
                self.logger.info(f"💡 Git push skipped: {e.stderr.strip()}")
    
        phase_end = time.time()
        self.logger.info(f"✨ Agent {agent_name} completed {phase_name} phase in {phase_end - phase_start:.2f} seconds")
    
        return modified_files, final_state

    def _generate_map_maintenance_prompt(self, tree_structure=None):
        """
        Generate map maintenance prompt for updating map.md.
        
        Args:
            tree_structure (list, optional): Current project tree structure
            
        Returns:
            str: Formatted map maintenance prompt
        """
        self.logger.debug("Generating map maintenance prompt...")

        # Add tree structure if provided
        structure_section = ""
        if tree_structure:
            tree_text = "\n".join(tree_structure)
            structure_section = f"""
# Current Project Structure
````
{tree_text}
````
"""
            self.logger.debug(f"Added tree structure with {len(tree_structure)} lines")

        # Core prompt content
        prompt = f"""{structure_section}
# Map Maintenance Instructions

Please update map.md to document the project structure. For each folder and file:

## 1. Folder Documentation
Document each folder with:
```markdown
### 📁 folder_name/
- **Purpose**: Main responsibility
- **Contains**: What belongs here
- **Usage**: When to use this folder
```

## 2. File Documentation
Document each file with:
```markdown
- **filename** (CATEGORY) - Role and purpose in relation to the mission, in relation to the folder. When to use it.
```

## File Categories:
- PRIMARY 📊 - Core project files
- SPEC 📋 - Specifications
- IMPL ⚙️ - Implementation
- DOCS 📚 - Documentation
- CONFIG ⚡ - Configuration
- UTIL 🛠️ - Utilities
- TEST 🧪 - Testing
- DATA 💾 - Data files

## Guidelines:
1. Focus on clarity and organization
2. Use consistent formatting
3. Keep descriptions concise but informative
4. Ensure all paths are documented
5. Maintain existing structure in map.md

Update map.md to reflect the current project structure while maintaining its format.
"""

        self.logger.debug("Generated map maintenance prompt")
        return prompt

    def _get_complete_tree(self):
        """Get complete tree structure without depth limit."""
        fs_utils = FSUtils()
        current_path = "."
        files = fs_utils.get_folder_files(current_path)
        subfolders = fs_utils.get_subfolders(current_path)
        return fs_utils.build_tree_structure(
            current_path=current_path,
            files=files,
            subfolders=subfolders,
            max_depth=None  # No depth limit
        )

    async def _execute_aider(self, cmd):
        """Execute aider command and handle results."""
        try:
            # Configure git to use UTF-8 for commit messages
            subprocess.run(['git', 'config', 'i18n.commitEncoding', 'utf-8'], check=True)
            subprocess.run(['git', 'config', 'i18n.logOutputEncoding', 'utf-8'], check=True)
            
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
            production_files, production_state = await self._run_aider_phase(
                cmd, agent_name, "🏭 Production", 
                "--> Focus on the Production Objective"
            )

            # Run role-specific phase
            role_files, role_state = await self._run_aider_phase(
                cmd, agent_name, "👤 Role-specific",
                "--> Focus on the Role-specific Objective"
            )

            # Run final check phase
            final_files, final_state = await self._run_aider_phase(
                cmd, agent_name, "🔍 Final Check",
                "--> Any additional changes required? Then update the todolist to reflect the changes."
            )

            # Get list of all modified/added/deleted files
            all_changes = set()
            all_changes.update(production_files or [])
            all_changes.update(role_files or [])
            all_changes.update(final_files or [])

            # Log total duration and summary
            total_duration = time.time() - start_time
            self.logger.info(f"🎯 Agent {agent_name} completed total aider execution in {total_duration:.2f} seconds")
            
            if all_changes:
                self.logger.info(f"📝 Agent {agent_name} modified total of {len(all_changes)} files")

        except Exception as e:
            agent_msg = f"Agent {agent_name} " if agent_name else ""
            self.logger.error(f"💥 {agent_msg}aider execution failed: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            if hasattr(e, 'output'):
                self.logger.error(f"Error output:\n{e.output}")
            raise
    def run_map_maintenance_for_all_folders(self):
        """Run map maintenance for each folder in the repository."""
        self.logger.debug("Starting map maintenance for all folders...")
        fs_utils = FSUtils()
        ignore_patterns = fs_utils._get_ignore_patterns()

        for root, dirs, _ in os.walk('.'):
            # Filter out ignored directories, especially .git and .aider folders
            dirs[:] = [d for d in dirs 
                      if not fs_utils._should_ignore(os.path.join(root, d), ignore_patterns) 
                      and not d.startswith('.git')  # Explicitly exclude .git folders
                      and not d.startswith('.aider')]  # Explicitly exclude .aider folders
            
            for dir_name in dirs:
                folder_path = os.path.join(root, dir_name)
                self.logger.debug(f"Initiating map maintenance for folder: {folder_path}")
                self.run_map_maintenance(folder_path)

    def run_map_maintenance(self, folder_path):
        """Perform map maintenance for a specific folder."""
        self.logger.debug(f"Running map maintenance for folder: {folder_path}")
        
        try:
            # Get the COMPLETE tree structure starting from root
            fs_utils = FSUtils()
            fs_utils.set_current_folder(folder_path)  # Set current folder before building tree
        
            root_files = fs_utils.get_folder_files(".")
            root_subfolders = fs_utils.get_subfolders(".")
            tree_structure = fs_utils.build_tree_structure(
                current_path=".",  # Start from root
                files=root_files,
                subfolders=root_subfolders,
                max_depth=None  # No depth limit to get full tree
            )

            # Generate the map maintenance prompt with full tree
            map_prompt = self._generate_map_maintenance_prompt(
                tree_structure=tree_structure
            )
            
            self.logger.debug(f"Generated map maintenance prompt:\n{map_prompt}")

            # Execute aider with the generated prompt
            cmd = ["python", "-m", "aider"]
            cmd.extend([
                "--model", "gpt-4o-mini",
                "--edit-format", "diff", 
                "--no-pretty",
                "--no-fancy-input",
                "--encoding", "utf-8",
                "--file", "map.md",  # Always update map.md
                "--message", map_prompt
            ])

            # Execute aider and capture output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='replace'
            )
            stdout, stderr = process.communicate()
            
            self.logger.debug(f"Aider response:\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")

            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd, stdout, stderr)
                
            self.logger.info(f"✅ Map maintenance completed for {folder_path}")
            
        except Exception as e:
            self.logger.error(f"Map maintenance failed for {folder_path}: {str(e)}")
            raise
