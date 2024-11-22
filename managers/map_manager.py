import os
import asyncio
import random
import subprocess
from pathlib import Path
import fnmatch
from utils.logger import Logger
import openai
import tiktoken
from dotenv import load_dotenv

class MapManager:
    """Manager class for generating context maps for agent operations."""
    
    def __init__(self):
        self.logger = Logger()
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in environment variables")

    def _get_ignore_patterns(self):
        """Get patterns from .gitignore and .aiderignore."""
        patterns = []
        
        # Always exclude these patterns
        patterns.extend([
            '.git*',
            '.aider*'
        ])
        
        # Read .gitignore
        if os.path.exists('.gitignore'):
            with open('.gitignore', 'r') as f:
                patterns.extend(line.strip() for line in f if line.strip() and not line.startswith('#'))
                
        # Read .aiderignore
        if os.path.exists('.aiderignore'):
            with open('.aiderignore', 'r') as f:
                patterns.extend(line.strip() for line in f if line.strip() and not line.startswith('#'))
                
        return patterns

    def _should_ignore(self, file_path, ignore_patterns):
        """Check if file should be ignored based on patterns."""
        # Always protect suivi.md
        if file_path == 'suivi.md' or file_path.endswith('/suivi.md'):
            return True
            
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

    def _get_available_files(self):
        """Get list of available files respecting ignore patterns."""
        ignore_patterns = self._get_ignore_patterns()
        available_files = []
        
        # Track folders to check for duplicate files
        folder_names = set()
        files_to_remove = []
        inaccessible_paths = set()
        
        # First pass: collect folder names
        for root, dirs, _ in os.walk('.', followlinks=False):
            dirs[:] = [d for d in dirs if not any(
                fnmatch.fnmatch(os.path.join(root, d), pattern) 
                for pattern in ignore_patterns
            )]
            
            for dir_name in dirs:
                try:
                    folder_path = os.path.join(root, dir_name)
                    # Test if we have permission to access the directory
                    if not os.access(folder_path, os.R_OK):
                        self.logger.warning(f"⚠️ No permission to access directory: {folder_path}")
                        inaccessible_paths.add(folder_path)
                        dirs.remove(dir_name)
                        continue
                        
                    # Convert to relative path with forward slashes
                    rel_folder_path = os.path.relpath(folder_path, '.').replace(os.sep, '/')
                    folder_names.add(rel_folder_path)
                except OSError as e:
                    self.logger.warning(f"⚠️ Cannot access directory {dir_name}: {str(e)}")
                    inaccessible_paths.add(os.path.join(root, dir_name))
                    dirs.remove(dir_name)
        
        # Second pass: collect files and check for duplicates
        for root, dirs, files in os.walk('.', followlinks=False):
            # Skip directories we couldn't access
            if any(root.startswith(p) for p in inaccessible_paths):
                continue
                
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    
                    # Check if we have permission to read the file
                    if not os.access(file_path, os.R_OK):
                        self.logger.warning(f"⚠️ No permission to read file: {file_path}")
                        continue
                        
                    # Convert to relative path with forward slashes
                    rel_path = os.path.relpath(file_path, '.').replace(os.sep, '/')
                    
                    # Skip files matching ignore patterns
                    if not any(fnmatch.fnmatch(rel_path, pattern) for pattern in ignore_patterns):
                        # Check if there's a folder with the same name (without extension)
                        file_base = os.path.splitext(rel_path)[0]
                        if file_base in folder_names:
                            self.logger.warning(f"⚠️ Found file '{rel_path}' that has same name as folder - will be removed")
                            if os.access(file_path, os.W_OK):
                                files_to_remove.append(file_path)
                            else:
                                self.logger.warning(f"⚠️ No permission to remove file: {file_path}")
                        else:
                            available_files.append(rel_path)
                            
                except OSError as e:
                    self.logger.warning(f"⚠️ Cannot access file {file}: {str(e)}")
        
        # Remove duplicate files
        for file_to_remove in files_to_remove:
            try:
                os.remove(file_to_remove)
                self.logger.success(f"🗑️ Removed duplicate file: {file_to_remove}")
            except Exception as e:
                self.logger.error(f"❌ Failed to remove duplicate file {file_to_remove}: {str(e)}")
        
        return sorted(available_files)  # Sort for consistent output

    def generate_map(self, mission_filepath=".aider.mission.md", 
                    objective_filepath=None, 
                    agent_filepath=None):
        """Generate a context map for an agent."""
        try:
            # Extract agent name from filepath
            agent_name = self._extract_agent_name(agent_filepath)
            self.logger.info(f"🗺️ Generating map for agent: {agent_filepath}")
            
            # Validate input files
            if not all(self._validate_file(f) for f in [mission_filepath, objective_filepath, agent_filepath]):
                raise ValueError("Invalid or missing input files")
                
            # Load required content
            mission_content = self._read_file(mission_filepath)
            objective_content = self._read_file(objective_filepath)
            agent_content = self._read_file(agent_filepath)
            
            # Get available files
            available_files = self._get_available_files()
            
            # Generate map via GPT
            context_map = self._generate_map_content(
                mission_content, 
                objective_content, 
                agent_content,
                available_files
            )
            
            # Save map using extracted agent name
            output_path = f".aider.map.{agent_name}.md"
            self._save_map(output_path, context_map)
            
            self.logger.info(f"✅ Successfully generated context map for {agent_name}")
            
        except Exception as e:
            self.logger.error(f"❌ Map generation failed: {str(e)}")
            raise

    def _validate_file(self, filepath):
        """Validate file exists and is readable."""
        return filepath and os.path.exists(filepath) and os.access(filepath, os.R_OK)

    def _extract_agent_name(self, agent_filepath):
        """Extract agent name from filepath."""
        basename = os.path.basename(agent_filepath)
        return basename.replace('.aider.agent.', '').replace('.md', '')

    def _read_file(self, filepath):
        """Read content from file with fallback encoding support."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback encodings if UTF-8 fails
            for encoding in ['latin-1', 'cp1252']:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        content = f.read()
                        # Convert to UTF-8
                        return content.encode(encoding).decode('utf-8')
                except UnicodeDecodeError:
                    continue
            raise UnicodeDecodeError(f"Failed to read {filepath} with any supported encoding")
        except Exception as e:
            self.logger.error(f"Error reading file {filepath}: {str(e)}")
            raise

    def _generate_map_content(self, mission_content, objective_content, agent_content, available_files):
        """Generate context map content using GPT."""
        try:
            client = openai.OpenAI()
            prompt = self._create_map_prompt(
                mission_content, 
                objective_content, 
                agent_content  # Removed available_files argument
            )
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """
{agent_content}

# Mapping process
You are asked to be a context mapping system that selects relevant files for an agent's next operation.
Your task is to analyze the mission, objective, and agent configuration to determine which files from the available list are needed.

Output format must be a simple markdown list of files:

# Context Map
- file1.py
- path/to/file2.md
- etc.

Select only files that are directly relevant to the current objective.
"""},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            context_map = response.choices[0].message.content
            return context_map
            
        except Exception as e:
            self.logger.error(f"GPT API call failed: {str(e)}")
            raise

    def _create_map_prompt(self, mission_content, objective_content, agent_content):
        """Create prompt for context map generation."""
        # Load global map content if it exists
        global_map_content = ""
        if os.path.exists("map.md"):
            try:
                with open("map.md", 'r', encoding='utf-8') as f:
                    global_map_content = f.read()
            except Exception as e:
                self.logger.warning(f"⚠️ Could not read global map: {str(e)}")
                
        return f"""Based on the following context, analyze and select the relevant files needed for the next operation.

# Mission
````
{mission_content}
````

# Global Project Map
The following describes all files in the project and their purposes:
````
{global_map_content}
````

# Current Objective
````
{objective_content}
````

Using the project map descriptions, carefully analyze:

1. MODIFICATIONS NEEDED:
   - Which files need to be changed to implement the objective
   - What specific changes are required in each file
   - How these changes align with each file's documented purpose

2. CONTEXT REQUIRED:
   - Which files provide essential background information
   - What specific knowledge each file contributes
   - How this context supports the planned changes

3. SYSTEM IMPACT:
   - How modifications might affect related files
   - Which dependencies need to be considered
   - What potential risks need to be managed

Provide your response in this format:

# Context Map
Files to modify:
- file1.py - [Current role: X] [Changes needed: Y] [Impact: Z]
- file2.md - [Current role: X] [Changes needed: Y] [Impact: Z]

Context files:
- file3.py - [Purpose: X] [Relevant aspects: Y] [Relationship to changes: Z]
- file4.md - [Purpose: X] [Relevant aspects: Y] [Relationship to changes: Z]

Note: Select only the most relevant files (aim for 3-5 files to modify, 3-5 context files).
Justify each selection based on the file's documented purpose in the project map.
"""


    def _remove_file_from_map(self, filepath):
        """Remove a file entry from the map."""
        try:
            map_path = "map.md"
            if not os.path.exists(map_path):
                return

            updated_lines = []
            with open(map_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Keep all lines except the one starting with filepath
            updated_lines = [line for line in lines if not line.strip().startswith(filepath)]
                
            # Write updated map if content changed
            if len(updated_lines) != len(lines):
                with open(map_path, 'w', encoding='utf-8') as f:
                    f.writelines(updated_lines)
                    self.logger.info(f"🗑️ Removed {filepath} from global map")
                    
        except Exception as e:
            self.logger.debug(f"Could not remove {filepath} from map: {str(e)}")

    def _save_map(self, filepath, content):
        """Save context map content to file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            self.logger.error(f"Error saving map to {filepath}: {str(e)}")
            raise

    async def initialize_global_map(self):
        """Initialize or reset the global map file with summaries of all project files."""
        try:
            self.logger.info("🗺️ Initializing global project map...")
            
            # Initialize tokenizer for GPT-4
            self.logger.info("🔄 Initializing GPT-4 tokenizer...")
            tokenizer = tiktoken.encoding_for_model("gpt-4")
            
            # Get all available files
            self.logger.info("🔍 Scanning project directory for files...")
            available_files = self._get_available_files()
            total_files = len(available_files)
            self.logger.info(f"📊 Found {total_files} files to process")
            
            # Create map header
            map_content = "# Project Map\n\n"
            
            # Process files in batches of 10
            batch_size = 10
            total_batches = (total_files + batch_size - 1) // batch_size
            
            for i in range(0, total_files, batch_size):
                batch = available_files[i:i+batch_size]
                batch_tasks = []
                current_batch = i//batch_size + 1
                
                self.logger.info(f"📦 Processing batch {current_batch}/{total_batches} ({len(batch)} files)")
                
                # Create tasks for batch
                for filepath in batch:
                    try:
                        self.logger.debug(f"📄 Reading file: {filepath}")
                        with open(filepath, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        token_count = len(tokenizer.encode(file_content))
                        self.logger.debug(f"📊 File {filepath}: {token_count} tokens")
                        
                        # Create task for file summary generation
                        task = asyncio.create_task(self._generate_file_summary_async(filepath, file_content))
                        batch_tasks.append((filepath, token_count, task))
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not read {filepath}: {str(e)}")
                        continue
                
                # Wait for all summaries in batch
                self.logger.info(f"⏳ Generating summaries for batch {current_batch}...")
                for filepath, token_count, task in batch_tasks:
                    try:
                        summary = await task
                        map_content += f"{filepath} ({token_count} tokens) {summary}\n"
                        self.logger.debug(f"✅ Generated summary for {filepath}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not process {filepath}: {str(e)}")
                        continue
                
                # Log batch completion and progress
                progress = (current_batch / total_batches) * 100
                self.logger.info(f"✨ Completed batch {current_batch}/{total_batches} ({progress:.1f}%)")
                
                # Small delay between batches to avoid rate limits
                if current_batch < total_batches:
                    self.logger.debug("⏸️ Brief pause between batches...")
                    await asyncio.sleep(1)
                    
            # Save map file
            self.logger.info("💾 Saving global map file...")
            with open("map.md", 'w', encoding='utf-8') as f:
                f.write(map_content)
                
            self.logger.success(f"""✨ Global project map initialized:
   - Processed {total_files} files
   - Generated {total_batches} batches
   - Created comprehensive project map""")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize global map: {str(e)}")
            raise

    def update_global_map(self, modified_file_path, force_refresh=False):
        """
        Update global map with latest file summary after a commit.
        
        Args:
            modified_file_path (str): Path to the modified file
            force_refresh (bool): If True, always generate new description regardless of random chance
        """
        try:
            # First decode the path if it's already encoded
            if isinstance(modified_file_path, str):
                # Remove any extra quotes
                modified_file_path = modified_file_path.strip('"')
                # Normalize path encoding
                try:
                    # Try to decode if it's encoded
                    modified_file_path = bytes(modified_file_path, 'utf-8').decode('unicode-escape')
                except:
                    # If decoding fails, use the path as-is
                    pass

            # First check if file exists - if not, just remove from map and return
            if not os.path.exists(modified_file_path):
                self._remove_file_from_map(modified_file_path)
                self.logger.info(f"🗑️ Removed non-existent file from map: {modified_file_path}")
                return

            # First check if file needs splitting
            from managers.redundancy_manager import RedundancyManager
            redundancy_mgr = RedundancyManager()
            
            # Only attempt split if file exists (might have been deleted)
            if os.path.exists(modified_file_path):
                try:
                    # Attempt to split if needed
                    was_split = redundancy_mgr.split_file(modified_file_path)
                    if was_split:
                        self.logger.success(f"🔄 Split {modified_file_path} into sections")
                        # Update map for each new file with force_refresh=True
                        dir_name = os.path.splitext(modified_file_path)[0]
                        for new_file in os.listdir(dir_name):
                            new_file_path = os.path.join(dir_name, new_file)
                            self.update_global_map(new_file_path, force_refresh=True)
                        return
                except Exception as e:
                    self.logger.error(f"❌ Failed to check/split file {modified_file_path}: {str(e)}")
                    # Continue with normal map update even if split fails

            # Read current global map content with UTF-8 encoding
            global_map_content = ""
            if os.path.exists("map.md"):
                try:
                    with open("map.md", 'r', encoding='utf-8') as f:
                        global_map_content = f.read()
                except UnicodeDecodeError:
                    # Fallback encodings if UTF-8 fails
                    for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                        try:
                            with open("map.md", 'r', encoding=encoding) as f:
                                global_map_content = f.read()
                                break
                        except UnicodeDecodeError:
                            continue

            # Read modified file content with robust encoding handling
            file_content = None
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(modified_file_path, 'r', encoding=encoding) as f:
                        file_content = f.read()
                        break
                except UnicodeDecodeError:
                    continue

            if file_content is None:
                raise ValueError(f"Could not read {modified_file_path} with any supported encoding")

            # Get token count
            # Get last commit message for this file
            try:
                commit_msg = subprocess.check_output(
                    ['git', 'log', '-1', '--pretty=format:%s', modified_file_path],
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                ).strip()
            except subprocess.CalledProcessError:
                commit_msg = "No commit message found"

            tokenizer = tiktoken.encoding_for_model("gpt-4")
            token_count = len(tokenizer.encode(file_content))

            # Always generate new description if force_refresh is True
            should_update_description = force_refresh or random.random() < 0.10

            if should_update_description:
                # Generate new summary with global context
                client = openai.OpenAI()
                prompt = self._generate_file_summary_prompt(modified_file_path, file_content, global_map_content, commit_msg)

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a technical analyst specializing in identifying unique characteristics and differentiating features of files within a project."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=200
                )

                summary = response.choices[0].message.content.strip()
                # Log when we generate a new description
                self.logger.success(f"📝 {modified_file_path} : {summary}")
            else:
                # Get existing summary from map if available
                summary = self._get_existing_summary(global_map_content, modified_file_path)
                if not summary:
                    summary = "File updated"  # Fallback if no existing summary
                # Log simple modification notice with commit message
                self.logger.success(f"Modified file: {modified_file_path} ({commit_msg})")

            # Update map.md with new or existing summary
            # Always write with UTF-8 encoding
            try:
                self._update_map_file(modified_file_path, token_count, summary)
            except Exception as e:
                self.logger.error(f"Failed to update map file: {str(e)}")
                # Try to write with a more permissive encoding if UTF-8 fails
                self._update_map_file_fallback(modified_file_path, token_count, summary)

            self.logger.debug(f"🔄 Updated global map for: {modified_file_path}")

        except Exception as e:
            self.logger.error(f"Failed to update global map: {str(e)}")
            raise

    async def _generate_file_summary_async(self, filepath, content):
        """Async version of file summary generation."""
        try:
            # Read current global map content
            global_map_content = ""
            if os.path.exists("map.md"):
                with open("map.md", 'r', encoding='utf-8') as f:
                    global_map_content = f.read()

            client = openai.OpenAI()
            prompt = self._generate_file_summary_prompt(filepath, content)
            
            response = await asyncio.to_thread(
                lambda: client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a technical analyst specializing in identifying unique characteristics and differentiating features of files within a project."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=200
                )
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to generate file summary: {str(e)}")
            raise

    def _get_existing_summary(self, map_content, file_path):
        """Extract existing summary for a file from the map content."""
        try:
            for line in map_content.split('\n'):
                if line.startswith(file_path):
                    # Extract summary part after token count
                    parts = line.split(')')
                    if len(parts) > 1:
                        return parts[1].strip()
        except Exception as e:
            self.logger.debug(f"Could not extract existing summary: {str(e)}")
        return None

    def _update_map_file(self, filepath, token_count, summary):
        """Update map.md with new file summary."""
        try:
            # First check if file exists, if not just return silently
            if not os.path.exists(filepath):
                # Remove entry from map if it exists
                self._remove_file_from_map(filepath)
                return

            map_path = "map.md"
            updated_lines = []
            file_entry = f"{filepath} ({token_count} tokens) {summary}"
            entry_updated = False
            
            # Read existing map if it exists
            if os.path.exists(map_path):
                with open(map_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # Update existing entry or keep line
                for line in lines:
                    if line.strip().startswith(filepath):
                        updated_lines.append(file_entry + '\n')
                        entry_updated = True
                    else:
                        updated_lines.append(line)
                    
            # Add new entry if not updated
            if not entry_updated:
                if not updated_lines:  # New file
                    updated_lines.append("# Project Map\n\n")
                updated_lines.append(file_entry + '\n')
                
            # Write updated map
            with open(map_path, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
                
        except Exception as e:
            self.logger.error(f"Failed to update map file: {str(e)}")
            raise

    def _create_map_prompt(self, mission_content, objective_content, agent_content):
        """Create prompt for context map generation."""
        # Load global map content if it exists
        global_map_content = ""
        if os.path.exists("map.md"):
            try:
                with open("map.md", 'r', encoding='utf-8') as f:
                    global_map_content = f.read()
            except Exception as e:
                self.logger.warning(f"⚠️ Could not read global map: {str(e)}")
                    
        return f"""Based on the following context, analyze and select the relevant files needed for the next operation.

# Mission
````
{mission_content}
````

# Global Project Map
The following describes all files in the project and their purposes:
````
{global_map_content}
````

# Current Objective
````
{objective_content}
````

For each file, you must:

1. IDENTIFY PRIMARY DELIVERABLES:
   - Which files are the main outputs/deliverables
   - What is their role in fulfilling the mission
   - How other files support these deliverables

2. ESTABLISH FILE RELATIONSHIPS:
   - How each file relates to primary deliverables
   - Whether files are source data, analysis tools, or outputs
   - Clear hierarchy of file importance to mission

3. DESCRIBE FUNCTIONAL ROLES:
   - Use CAPS to indicate file role (e.g., PRIMARY DELIVERABLE, SOURCE DATA)
   - Explain how file supports mission objectives
   - Show clear connection to main deliverables

Format your response as:

# Context Map
filename.md (token_count tokens) 📊 ROLE - Clear description of how this file supports the mission's primary deliverables.

Example entries:
- analysis.md (358 tokens) 📊 PRIMARY DELIVERABLE - Synthesizes insights from all summaries to document key findings.
- summaries/*.md (various tokens) 📚 READ-ONLY SOURCE DATA - Provides raw data for analysis.md.
- helpers/*.md (various tokens) 🛠️ SUPPORT TOOLS - Contains utilities that assist in generating analysis.md.

Note:
- Use CAPS for file roles
- Show clear relationship to primary deliverables
- Indicate if files are read-only or meant to be modified
- Use appropriate emojis to indicate file purpose
- Keep descriptions focused on mission support
"""

    def _update_map_file_fallback(self, filepath, token_count, summary):
        """Fallback method to update map file with alternative encodings."""
        try:
            map_path = "map.md"
            updated_lines = []
            file_entry = f"{filepath} ({token_count} tokens) {summary}"
            entry_updated = False
            
            # Try reading with different encodings
            content = None
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    if os.path.exists(map_path):
                        with open(map_path, 'r', encoding=encoding) as f:
                            lines = f.readlines()
                            
                        # Update existing entry or keep line
                        for line in lines:
                            if line.strip().startswith(filepath):
                                updated_lines.append(file_entry + '\n')
                                entry_updated = True
                            else:
                                updated_lines.append(line)
                        
                        content = True
                        break
                except UnicodeDecodeError:
                    continue
                    
            if content is None:
                raise ValueError(f"Could not read {map_path} with any supported encoding")

            # Add new entry if not updated
            if not entry_updated:
                if not updated_lines:  # New file
                    updated_lines.append("# Project Map\n\n")
                updated_lines.append(file_entry + '\n')
                
            # Try writing with different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(map_path, 'w', encoding=encoding) as f:
                        f.writelines(updated_lines)
                    break
                except UnicodeEncodeError:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to update map file with fallback method: {str(e)}")
            raise
