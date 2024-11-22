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
        repo_viz_path = self._get_repo_visualizer_path()
        dist_path = os.path.join(repo_viz_path, 'dist')
        index_js = os.path.join(dist_path, 'index.js')
        
        if not os.path.exists(repo_viz_path):
            raise FileNotFoundError(
                f"repo-visualizer not found at {repo_viz_path}. "
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

    def run_aider(self, objective_filepath, map_filepath, agent_filepath, model="gpt-4o-mini"):
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
            
            # Ensure aider is installed
            self._ensure_aider_installed()
            
            # Validate input files
            if not self._validate_files(objective_filepath, map_filepath, agent_filepath):
                raise ValueError("Invalid or missing input files")
                
            # Load context map
            context_files = self._load_context_map(map_filepath)
            
            # Configure aider command
            cmd = self._build_aider_command(
                objective_filepath,
                map_filepath,
                agent_filepath,
                context_files,
                model=model
            )
            
            # Execute aider
            self._execute_aider(cmd)
            
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
            "--cache-prompts",
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
    
        # Push changes to GitHub if files were modified
        if modified_files:
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

    def _generate_map_maintenance_prompt(self, changed_files=None, tree_structure=None):
        """
        Generate comprehensive map maintenance prompt.
        
        Args:
            changed_files (set, optional): Set of files that were modified
            tree_structure (list, optional): Current project tree structure
            
        Returns:
            str: Formatted map maintenance prompt
        """
        # Build changes section if files were changed
        changes_section = ""
        if changed_files:
            changes_section = f"""
# Project Structure Changes
The following files were modified in this session:
{', '.join(changed_files)}
"""

        # Add tree structure if provided
        structure_section = ""
        if tree_structure:
            tree_text = "\n".join(tree_structure)
            structure_section = f"""
# Current Complete Project Structure
````
{tree_text}
````
"""

        # Core prompt content
        return f"""{changes_section}{structure_section}
# Instructions for Map Maintenance

## 1. Folder Documentation
For each folder, document:
- **Purpose**: What is this folder's main responsibility
- **Parent Relationship**: How does it serve its parent folder's purpose
- **Content Guidelines**: What should/shouldn't be placed here
- **Usage Context**: When to add files here vs other locations

Format:
```markdown
### 📁 folder_name/
- **Purpose**: [Main responsibility of this folder]
- **Serves Parent**: [How it helps parent folder's mission]
- **Contains**: [What belongs here]
- **When to Use**: [Usage guidelines]
```

## 2. File Documentation
For each file, document:
- **Role**: How it contributes to its folder's purpose
- **Usage**: When and how to use this file
- **Dependencies**: What it relies on or what relies on it
- **Category**: Use appropriate category and emoji

Format:
```markdown
- **filename** (CATEGORY EMOJI) - [Role in folder] | Used for [purpose] | Dependencies: [list]
```

## 3. Categories and Emojis
Core Files:
- PRIMARY 📊 - Essential project infrastructure
- SPEC 📋 - Specifications and requirements
- IMPL ⚙️ - Core implementation files
- DOCS 📚 - Documentation and guides

Support Files:
- CONFIG ⚡ - Configuration and settings
- UTIL 🛠️ - Utility and helper functions
- TEST 🧪 - Testing and validation
- BUILD 📦 - Build and deployment

Working Files:
- WORK ✍️ - In-progress work
- DRAFT 📝 - Draft documents
- TEMPLATE 📄 - Templates and boilerplate
- ARCHIVE 📂 - Archived content

Data Files:
- SOURCE 💾 - Original source data
- GEN ⚡ - Generated content
- CACHE 💫 - Temporary/cache data
- BACKUP 💿 - Backup files

## 4. Update Process
1. Start from root directory
2. For each folder:
   - Add/update folder documentation
   - Document relationships with parent/sibling folders
   - Specify content guidelines
3. For each file:
   - Add/update file documentation
   - Ensure category matches current role
   - Document dependencies and usage
4. For modified files:
   - Update descriptions to reflect new purpose
   - Verify category still appropriate
5. For deleted files:
   - Remove entries from map
   - Update related dependency references

## 5. Validation
- Every folder must have complete documentation
- Every file must have a description and category
- All relationships must be documented
- Categories must accurately reflect current usage
- Dependencies must be explicitly stated
- Usage guidelines must be clear and specific

Update map.md to reflect these changes while maintaining its current structure and format.
Focus on making the relationships and usage patterns clear and explicit.
"""

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

    def _execute_aider(self, cmd):
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
            production_files, production_state = self._run_aider_phase(
                cmd, agent_name, "🏭 Production", 
                "--> Focus on the Production Objective"
            )

            # Run role-specific phase
            role_files, role_state = self._run_aider_phase(
                cmd, agent_name, "👤 Role-specific",
                "--> Focus on the Role-specific Objective"
            )

            # Run final check phase
            final_files, final_state = self._run_aider_phase(
                cmd, agent_name, "🔍 Final Check",
                "--> Any additional changes required? Then update the todolist to reflect the changes."
            )

            # Get list of all modified/added/deleted files
            all_changes = set()
            all_changes.update(production_files or [])
            all_changes.update(role_files or [])
            all_changes.update(final_files or [])

            if all_changes:
                self.logger.info("🗺️ Starting map maintenance phase")
                
                # Get complete tree structure
                tree_structure = self._get_complete_tree()
                tree_text = "\n".join(tree_structure)
                
                # Generate map maintenance prompt
                map_prompt = self._generate_map_maintenance_prompt(
                    changed_files=all_changes,
                    tree_structure=tree_structure
                )
                
                # Run map maintenance phase
                map_cmd = cmd.copy()
                map_cmd.extend(['--file', 'map.md'])  # Add map.md as editable
                map_cmd[-1] = map_prompt  # Replace message with map maintenance prompt
                
                self.logger.debug("🔄 Running map maintenance phase")
                map_files, map_state = self._run_aider_phase(
                    map_cmd, agent_name, "🗺️ Map Maintenance", 
                    "--> Update map.md to reflect all project changes"
                )

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
    def run_map_maintenance(self):
        """Placeholder for map maintenance logic."""
        self.logger.info("Running map maintenance...")
        # Implement map maintenance logic here
