import os
import asyncio
import random
import subprocess
import logging
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
        self.api_semaphore = asyncio.Semaphore(10)  # Limit concurrent API calls
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")

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
        """Generate a hierarchical context map for an agent."""
        try:
            # Extract agent name from filepath
            agent_name = self._extract_agent_name(agent_filepath)
            self.logger.info(f"🗺️ Generating hierarchical map for agent: {agent_filepath}")
            
            # Validate input files
            if not all(self._validate_file(f) for f in [mission_filepath, objective_filepath, agent_filepath]):
                raise ValueError("Invalid or missing input files")
                
            # Load required content
            mission_content = self._read_file(mission_filepath)
            objective_content = self._read_file(objective_filepath)
            
            # Initialize complete map content
            complete_map = ["# Project Map\n"]
            
            # Process root directory first
            root_analysis = self._generate_map_content(
                ".",
                mission_content,
                objective_content
            )
            complete_map.append(root_analysis)
            
            # Process each subdirectory
            for root, dirs, _ in os.walk("."):
                # Skip ignored directories
                dirs[:] = [d for d in dirs if not self._should_ignore(
                    os.path.join(root, d), 
                    self._get_ignore_patterns()
                )]
                
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    # Generate map for this directory
                    dir_analysis = self._generate_map_content(
                        dir_path,
                        mission_content,
                        objective_content
                    )
                    complete_map.append(dir_analysis)
            
            # Save complete map
            output_path = f".aider.map.{agent_name}.md"
            self._save_map(output_path, "\n\n".join(complete_map))
            
            self.logger.info(f"✅ Successfully generated hierarchical map for {agent_name}")
            
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

    def _generate_map_content(self, mission_content, objective_content, agent_content):
        """Generate context map content using GPT."""
        try:
            client = openai.OpenAI()
            prompt = self._create_map_prompt(
                mission_content, 
                objective_content, 
                agent_content
            )
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """
{agent_content}

# Mapping process
You are asked to be a context mapping system that selects relevant files for an agent's next operation.
Your task is to analyze the mission, objective, and agent configuration to determine which files from the available list are needed."""},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Get raw content
            content = response.choices[0].message.content
            
            # Clean up the content:
            # 1. Split into lines
            lines = content.split('\n')
            # 2. Remove any lines starting with '#' (headers)
            # 3. Remove empty lines
            # 4. Ensure each line starts with '-'
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    if not line.startswith('-'):
                        line = f"- {line}"
                    cleaned_lines.append(line)
            
            # Join lines with single newlines
            context_map = "# Project Map\n\n" + "\n".join(cleaned_lines)
            
            return context_map
            
        except Exception as e:
            self.logger.error(f"GPT API call failed: {str(e)}")
            raise

    def _create_map_prompt(self, current_folder, mission_content, objective_content):
        """Create prompt for context map generation."""
        # Generate full tree structure
        full_tree = self._generate_tree_structure()
        
        # Get files in current folder
        files_in_folder = self._get_files_in_folder(current_folder)
        
        # Load global map for context
        global_map = ""
        if os.path.exists("map.md"):
            try:
                with open("map.md", 'r', encoding='utf-8') as f:
                    global_map = f.read()
            except Exception as e:
                self.logger.warning(f"⚠️ Could not read global map: {str(e)}")

        return f"""Analyze this folder's contents and its place in the project structure.

# Mission
```
{mission_content}
```

# Current Objective
```
{objective_content}
```

# Current Folder: {current_folder}

# Complete Project Tree:
```
{full_tree}
```

# Files to Analyze in Current Folder:
```
{', '.join(files_in_folder)}
```

# Existing Global Map:
```
{global_map}
```

Analyze each file in this folder considering:

1. FOLDER CONTEXT:
   - How this folder supports project objectives
   - Why these files are grouped together
   - Relationship to parent/sibling folders

2. FILE ANALYSIS:
   - Role of each file in current folder
   - How it supports folder's purpose
   - Relationships between files

3. STRUCTURAL IMPACT:
   - How this level affects overall architecture
   - Dependencies with other folders
   - Integration points

Provide your response in this format:

## Folder Purpose
[Explain why this folder exists and its role in the project]

## File Mapping
[For each file in current folder only:]
- filename.ext (📊 ROLE) - Clear description showing:
  * Purpose in this folder
  * Relationship to other files
  * Support of project mission

Use these roles with corresponding emojis:

Core Project Files:
* PRIMARY DELIVERABLE (📊) - Final output files
* SPECIFICATION (📋) - Requirements and plans
* IMPLEMENTATION (⚙️) - Core functionality
* DOCUMENTATION (📚) - User guides and docs

Support Files:
* CONFIGURATION (⚡) - Settings and configs
* UTILITY (🛠️) - Helper functions
* TEST (🧪) - Test cases
* BUILD (📦) - Build scripts

Working Files:
* WORK DOCUMENT (✍️) - Active files
* DRAFT (📝) - In-progress work
* TEMPLATE (📄) - Reusable patterns
* ARCHIVE (📂) - Historical versions

Data Files:
* SOURCE DATA (💾) - Input data
* GENERATED (⚡) - Created outputs
* CACHE (💫) - Temporary data
* BACKUP (💿) - System backups"""


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

    def _generate_tree_structure(self, root_dir="."):
        """Generate a tree view of the project structure."""
        tree = []
        ignore_patterns = self._get_ignore_patterns()
        
        for root, dirs, files in os.walk(root_dir):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d), ignore_patterns)]
            
            level = root.replace(root_dir, '').count(os.sep)
            indent = '  ' * level
            tree.append(f"{indent}{os.path.basename(root)}/")
            
            # Add files at this level
            for f in sorted(files):
                if not self._should_ignore(os.path.join(root, f), ignore_patterns):
                    tree.append(f"{indent}  {f}")
                    
        return '\n'.join(tree)

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
            print("Starting map initialization...")  # Debug print
            self.logger.logger.setLevel(logging.DEBUG)  # Force debug level temporarily 
            self.logger.info("🗺️ Initializing global project map...")
            
            # Initialize tokenizer for GPT-4
            print("Initializing tokenizer...")  # Debug print
            self.logger.info("🔄 Initializing GPT-4 tokenizer...")
            tokenizer = tiktoken.encoding_for_model("gpt-4")
            
            # Get all available files
            print("Scanning for files...")  # Debug print
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
                current_batch = i//batch_size + 1
                
                self.logger.info(f"📦 Processing batch {current_batch}/{total_batches} ({len(batch)} files)")
                
                # Process batch files in parallel
                batch_tasks = []
                for filepath in batch:
                    try:
                        # Read file content
                        content = await self._read_file_async(filepath)
                        token_count = await self._count_tokens_async(content)
                        self.logger.debug(f"📊 File {filepath}: {token_count} tokens")
                        
                        # Create task for summary generation
                        task = self._generate_file_summary_async(filepath, content)
                        batch_tasks.append((filepath, token_count, task))
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not process {filepath}: {str(e)}")
                        continue
            
                # Wait for all summaries in batch
                self.logger.info(f"⏳ Generating summaries for batch {current_batch}...")
                for filepath, token_count, task in batch_tasks:
                    try:
                        summary = await task  # Await the task here
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
            # Normalize and validate file path
            file_path = self._normalize_file_path(modified_file_path)
            if not os.path.exists(file_path):
                self._remove_file_from_map(file_path)
                return

            # Handle file splitting if needed
            if self._handle_file_splitting(file_path):
                return

            # Get file content and token count
            content = self._read_file_with_encoding(file_path)
            token_count = self._count_tokens(content)

            # Generate file summary
            summary = self._generate_file_summary(file_path, content)

            # Update map file
            self._update_map_entry(file_path, token_count, summary)

        except Exception as e:
            self.logger.error(f"Failed to update global map: {str(e)}")
            raise
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
            tokenizer = tiktoken.encoding_for_model("gpt-4")
            token_count = len(tokenizer.encode(file_content))

            # Generate new summary with structural focus
            client = openai.OpenAI()
            prompt = self._generate_file_summary_prompt(modified_file_path, file_content, global_map_content)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a technical architect specializing in analyzing file roles and relationships within project structures."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )

            summary = response.choices[0].message.content.strip()
            self.logger.success(f"📝 {modified_file_path} : {summary}")

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

    async def _read_file_async(self, filepath):
        """Read file content asynchronously using thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._read_file, filepath)

    async def _count_tokens_async(self, content):
        """Count tokens asynchronously using thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: len(self.tokenizer.encode(content)))

    async def _generate_file_summary_async(self, filepath, content):
        """Generate file summary with rate limiting."""
        try:
            async with self.api_semaphore:
                mission_content = f"Analyze file: {filepath}"
                objective_content = "Generate file description"
                agent_content = "File summary generation"

                prompt = self._create_map_prompt(
                    mission_content,
                    objective_content,
                    agent_content
                )

                client = openai.OpenAI()
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

    def _generate_file_summary_prompt(self, filepath, content, global_map_content):
        """
        Generate a prompt focused on file's structural role in the project.
        
        Args:
            filepath (str): Path to the file being analyzed
            content (str): Content of the file
            global_map_content (str): Current global map content
            
        Returns:
            str: Prompt for GPT to analyze file's role
        """
        # Get directory structure context
        dir_name = os.path.dirname(filepath)
        file_name = os.path.basename(filepath)
        
        # Get sibling files in same directory
        sibling_files = []
        if os.path.exists(dir_name):
            sibling_files = [f for f in os.listdir(dir_name) 
                           if os.path.isfile(os.path.join(dir_name, f))
                           and f != file_name]

        return f"""Analyze this file's structural role in the project:

File: {filepath}
Directory: {dir_name}
Sibling Files: {', '.join(sibling_files)}

Content:
```
{content}
```

Current Project Map:
```
{global_map_content}
```

Focus your analysis on:
1. Why this file exists in this specific directory
2. How it relates to sibling files
3. Its role in the overall project structure
4. Technical concepts it implements
5. Key dependencies and relationships

Provide a concise one-line summary that explains:
- The file's technical role (marked in **bold**)
- Why it's in this directory
- How it supports the project architecture

Format: "File implements **[technical role]** to [purpose] by [implementation detail]"
"""

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

    def _read_file_with_encoding(self, filepath):
        """Read file content with robust encoding handling."""
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Could not read {filepath} with any supported encoding")

    def _write_file_with_encoding(self, filepath, content):
        """Write content to file with UTF-8 encoding."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            self.logger.error(f"Failed to write to {filepath}: {str(e)}")
            raise

    def _create_map_prompt(self, current_folder, mission_content, objective_content):
        """Create prompt for context map generation."""
        # Generate full tree structure
        full_tree = self._generate_tree_structure()
        
        # Get files in current folder
        files_in_folder = self._get_files_in_folder(current_folder)
        
        # Load global map for context
        global_map = ""
        if os.path.exists("map.md"):
            try:
                with open("map.md", 'r', encoding='utf-8') as f:
                    global_map = f.read()
            except Exception as e:
                self.logger.warning(f"⚠️ Could not read global map: {str(e)}")

        return f"""Analyze this folder's contents and its place in the project structure.

# Mission
```
{mission_content}
```

# Current Objective
```
{objective_content}
```

# Current Folder: {current_folder}

# Complete Project Tree:
```
{full_tree}
```

# Files to Analyze in Current Folder:
```
{', '.join(files_in_folder)}
```

# Existing Global Map:
```
{global_map}
```

Analyze each file in this folder considering:

1. FOLDER CONTEXT:
   - How this folder supports project objectives
   - Why these files are grouped together
   - Relationship to parent/sibling folders

2. FILE ANALYSIS:
   - Role of each file in current folder
   - How it supports folder's purpose
   - Relationships between files

3. STRUCTURAL IMPACT:
   - How this level affects overall architecture
   - Dependencies with other folders
   - Integration points

Provide your response in this format:

## Folder Purpose
[Explain why this folder exists and its role in the project]

## File Mapping
[For each file in current folder only:]
- filename.ext (📊 ROLE) - Clear description showing:
  * Purpose in this folder
  * Relationship to other files
  * Support of project mission

Use these roles with corresponding emojis:

Core Project Files:
* PRIMARY DELIVERABLE (📊) - Final output files
* SPECIFICATION (📋) - Requirements and plans
* IMPLEMENTATION (⚙️) - Core functionality
* DOCUMENTATION (📚) - User guides and docs

Support Files:
* CONFIGURATION (⚡) - Settings and configs
* UTILITY (🛠️) - Helper functions
* TEST (🧪) - Test cases
* BUILD (📦) - Build scripts

Working Files:
* WORK DOCUMENT (✍️) - Active files
* DRAFT (📝) - In-progress work
* TEMPLATE (📄) - Reusable patterns
* ARCHIVE (📂) - Historical versions

Data Files:
* SOURCE DATA (💾) - Input data
* GENERATED (⚡) - Created outputs
* CACHE (💫) - Temporary data
* BACKUP (💿) - System backups"""

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
