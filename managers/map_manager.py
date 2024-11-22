import os
import asyncio
import logging
import time
import fnmatch
from pathlib import Path
from utils.logger import Logger
from utils.encoding_utils import EncodingUtils
from utils.encoding_utils import EncodingUtils
import openai
import tiktoken
from dotenv import load_dotenv
from managers.vision_manager import VisionManager

class MapManager:
    """
    Manager class for generating and maintaining project structure maps.
    
    Responsible for:
    - Generating hierarchical maps of project structure
    - Maintaining global project map
    - Analyzing file roles and relationships
    - Tracking structural changes
    
    Attributes:
        logger (Logger): Logging utility instance
        tokenizer (tiktoken.Encoding): GPT tokenizer for content analysis
        api_semaphore (asyncio.Semaphore): Rate limiter for API calls
    """
    
    def __init__(self):
        """Initialize the map manager with required components."""
        self.logger = Logger()
        self.encoding_utils = EncodingUtils()
        self.project_root = os.path.abspath('.')  # Store absolute path of project root
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        self.api_semaphore = asyncio.Semaphore(10)
        self._initial_mapping_in_progress = False
        self._vision_manager = VisionManager()
    def _validate_path_in_project(self, path: str) -> bool:
        """
        Validate that a path is within the project directory.
        
        Args:
            path (str): Path to validate
            
        Returns:
            bool: True if path is within project, False otherwise
        """
        # Convert to absolute path
        abs_path = os.path.abspath(path)
        # Check if path is within project root
        return os.path.commonpath([abs_path, self.project_root]) == self.project_root

    def _analyze_folder_level(self, folder_path: str, files_content: dict, 
                            subfolders: list, mission_content: str, 
                            objective_content: str) -> dict:
        """
        Analyze a single folder level with its files and immediate subfolders.
        Uses batch analysis and caching for efficiency.
        
        Args:
            folder_path (str): Path to current folder
            files_content (dict): Dictionary of filename to file content
            subfolders (list): List of immediate subfolder names
            mission_content (str): Overall mission context
            objective_content (str): Current objective context
            
        Returns:
            dict: Folder analysis including:
                - path: Folder path
                - purpose: Folder's purpose
                - files: List of file analyses
                - relationships: Dict of folder relationships
                
        Raises:
            ValueError: If folder_path is invalid or missing
            TypeError: If input parameters have invalid types
            Exception: For other unexpected errors
        """
        # Generate cache key from folder contents
        cache_key = f"{folder_path}:{','.join(sorted(files_content.keys()))}:{','.join(sorted(subfolders))}"
        
        # Check cache first
        if hasattr(self, '_folder_cache'):
            cached = self._folder_cache.get(cache_key)
            if cached:
                self.logger.debug(f"Using cached analysis for {folder_path}")
                return cached
        else:
            self._folder_cache = {}
        try:
            self.logger.debug(f"Analyzing folder level: {folder_path}")
            
            # Input validation
            if not folder_path:
                raise ValueError("folder_path cannot be empty")
            if not isinstance(files_content, dict):
                raise TypeError("files_content must be a dictionary")
            if not isinstance(subfolders, list):
                raise TypeError("subfolders must be a list")
            
            # Path normalization and validation
            abs_folder_path = os.path.abspath(folder_path)
            self.logger.debug(f"Absolute folder path: {abs_folder_path}")
            
            if not self._validate_path_in_project(abs_folder_path):
                raise ValueError(f"Path {abs_folder_path} is outside project directory")
                
            # Generate cache key with truncated mission content
            cache_key = f"{folder_path}:{','.join(sorted(files_content.keys()))}:{','.join(sorted(subfolders))}:{mission_content[:500]}"
            
            # Get complete folder structure with full mission content
            folder_structure = {
                'path': abs_folder_path,
                'files': list(files_content.keys()),
                'subfolders': subfolders,
                'mission_context': mission_content  # Use full mission content
            }
        except Exception as e:
            self.logger.error(f"Failed to validate folder parameters: {str(e)}")
            raise
            
        try:
            # Validate folder exists
            if not os.path.exists(folder_path):
                raise ValueError(f"Folder does not exist: {folder_path}")
                
            if not os.path.isdir(folder_path):
                raise ValueError(f"Path is not a directory: {folder_path}")
            
            # Get folder context and analyze files in parallel
            folder_context = self._get_folder_context(
                folder_path=abs_folder_path,
                files=folder_structure['files'],
                subfolders=folder_structure['subfolders'],
                mission_content=folder_structure['mission_context']
            )
            
            self.logger.debug(f"Folder context: {folder_context}")
            
            # Batch analyze all files at once
            analyzed_files = self._analyze_files_batch(abs_folder_path, folder_structure['files'])
            
            # Validate and build result
            if not folder_context.get('purpose'):
                raise ValueError(f"Failed to determine purpose for {folder_path}")
            if not folder_context.get('relationships'):
                raise ValueError(f"Failed to determine relationships for {folder_path}")
            
            analysis_result = {
                'path': abs_folder_path,
                'purpose': folder_context['purpose'],
                'files': analyzed_files,
                'relationships': folder_context['relationships'],
                'structure': folder_structure
            }
            
            # Cache the result
            self._folder_cache[cache_key] = analysis_result
            
            self.logger.debug(f"Analysis result: {analysis_result}")
            
            # Generate SVG only if not during initial mapping
            if not self._initial_mapping_in_progress:
                asyncio.run(self._vision_manager.update_map())
                
            return analysis_result
            
        except Exception as e:
            self.logger.error(
                f"Failed to analyze folder level {folder_path}\n"
                f"Error type: {type(e).__name__}\n"
                f"Error details: {str(e)}"
            )
            raise

    def _analyze_folder_hierarchy(self, folder_path: str, mission_content: str, objective_content: str) -> dict:
        """
        Analyze folder and all its subfolders recursively, with complete context.
        
        Args:
            folder_path (str): Current folder to analyze
            mission_content (str): Overall mission context
            objective_content (str): Current objective context
            
        Returns:
            dict: Complete folder analysis including:
                - Folder purpose
                - File categorizations
                - Subfolder relationships
                - Structural context
                
        Raises:
            ValueError: If folder_path is invalid
            OSError: If folder cannot be accessed
            Exception: For other unexpected errors
        """
        try:
            # Mark start of initial mapping
            self._initial_mapping_in_progress = True
            
            # Validate and normalize path
            if not folder_path:
                raise ValueError("folder_path cannot be empty")
            
            # Convert to absolute path if relative
            folder_path = os.path.abspath(folder_path)
            
            if not os.path.exists(folder_path):
                raise ValueError(f"Folder does not exist: {folder_path}")
                
            if not os.path.isdir(folder_path):
                raise ValueError(f"Path is not a directory: {folder_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to validate folder path: {str(e)}")
            self._initial_mapping_in_progress = False  # Reset on error
            raise
            
        try:
            # Get immediate files and their contents
            files_content = {}
            for file in self._get_folder_files(folder_path):
                try:
                    file_path = os.path.join(folder_path, file)
                    
                    # Check if file is binary
                    if self._is_binary_file(file_path):
                        self.logger.debug(f"Skipping binary file: {file}")
                        continue
                        
                    # Try different encodings
                    for encoding in ['utf-8', 'latin1', 'cp1252']:
                        try:
                            with open(file_path, 'r', encoding=encoding) as f:
                                content = f.read()
                                files_content[file] = content
                                break
                        except UnicodeDecodeError:
                            continue
                    else:
                        self.logger.warning(f"Could not decode {file} with any supported encoding")
                        
                except (OSError, UnicodeDecodeError) as e:
                    self.logger.warning(f"Could not read {file}: {str(e)}")
                except Exception as e:
                    self.logger.error(f"Unexpected error reading {file}: {str(e)}")

            # Get subfolder structure
            subfolders = self._get_subfolders(folder_path)
            
            # Generate complete folder context
            folder_analysis = self._analyze_folder_level(
                folder_path=folder_path,
                files_content=files_content,
                subfolders=subfolders,
                mission_content=mission_content,
                objective_content=objective_content
            )

            # Recursively analyze subfolders
            folder_analysis['subfolders'] = {}
            for subfolder in subfolders:
                try:
                    subfolder_path = os.path.join(folder_path, subfolder)
                    folder_analysis['subfolders'][subfolder] = self._analyze_folder_hierarchy(
                        folder_path=subfolder_path,
                        mission_content=mission_content,
                        objective_content=objective_content
                    )
                except Exception as e:
                    self.logger.error(f"Failed to analyze subfolder {subfolder}: {str(e)}")
                    folder_analysis['subfolders'][subfolder] = {
                        'path': subfolder_path,
                        'purpose': f'Analysis failed: {str(e)}',
                        'files': [],
                        'relationships': {},
                        'subfolders': {}
                    }

            # Once complete analysis is done, generate SVG
            if folder_path == "." and self._initial_mapping_in_progress:
                self._initial_mapping_in_progress = False
                asyncio.run(self._vision_manager.update_map())

            return folder_analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze folder hierarchy for {folder_path}: {str(e)}")
            self._initial_mapping_in_progress = False  # Reset on error
            raise

    def _get_folder_files(self, folder_path: str) -> list:
        """Get list of files in folder, respecting ignore patterns."""
        ignore_patterns = self._get_ignore_patterns()
        files = []
        
        for entry in os.scandir(folder_path):
            if entry.is_file():
                rel_path = os.path.relpath(entry.path, '.')
                if not self._should_ignore(rel_path, ignore_patterns):
                    files.append(entry.name)
                    
        return sorted(files)

    def _get_subfolders(self, folder_path: str) -> list:
        """Get list of subfolders, respecting ignore patterns."""
        ignore_patterns = self._get_ignore_patterns()
        folders = []
        
        for entry in os.scandir(folder_path):
            if entry.is_dir():
                rel_path = os.path.relpath(entry.path, '.')
                if not self._should_ignore(rel_path, ignore_patterns):
                    folders.append(entry.name)
                    
        return sorted(folders)

    def _create_folder_context_prompt(self, folder_path: str, files: list, subfolders: list, mission_content: str) -> str:
        """Create prompt for analyzing folder context."""
        # Ensure we're using relative path
        if os.path.isabs(folder_path):
            folder_path = os.path.relpath(folder_path, self.project_root)
            
        # Build tree structure including both files and subfolders
        tree = ["📂 ./"]
        
        # Add files first
        for i, f in enumerate(files):
            prefix = "├─ " if (i < len(files) - 1 or subfolders) else "└─ "
            tree.append(f"   {prefix}{f}")
            
        # Add subfolders
        for i, d in enumerate(subfolders):
            prefix = "├─ " if i < len(subfolders) - 1 else "└─ "
            tree.append(f"   {prefix}{d}/")
        
        tree_str = "\n".join(tree)

        return f"""# Objective
Define folder's purpose and relationships:

# Current Folder Structure
{tree_str}

# Mission Context
````
{mission_content}
````

# Instructions
Provide in this format:
Purpose: 📁 [Action verb + direct object, max 10 words]
Parent: 🔼 [Direct relationship statement]
Siblings: 🔄 [Direct relationship statement]
Children: 🔽 [Direct relationship statement]

Rules:
- Start Purpose with action verb
- Use declarative statements
- Omit conditionals
- Maximum 10 words per line
- Focus on concrete actions
- Include emojis as shown in format"""

    def _get_folder_context_for_path(self, folder_path: str) -> dict:
        """
        Get folder context for a specific path.
        
        Args:
            folder_path (str): Path to get context for
            
        Returns:
            dict: Folder context including path and purpose
            
        Note:
            Uses simpler context generation since this is just for hierarchy display
        """
        try:
            # Convert to absolute path
            abs_path = os.path.abspath(folder_path)
            
            # Check cache first
            if hasattr(self, '_context_cache'):
                cached = self._context_cache.get(abs_path)
                if cached:
                    return cached
            
            # Get files and subfolders
            files = self._get_folder_files(abs_path)
            subfolders = self._get_subfolders(abs_path)
            
            # Get context with minimal mission content
            context = self._get_folder_context(
                folder_path=abs_path,
                files=files,
                subfolders=subfolders,
                mission_content="Analyze folder structure"  # Minimal context needed
            )
            
            return context
            
        except Exception as e:
            self.logger.warning(f"Could not get context for {folder_path}: {str(e)}")
            # Return minimal context on error
            return {
                'path': abs_path,
                'purpose': f"Storage folder for {os.path.basename(abs_path)} content",
                'relationships': {
                    'parent': 'No parent relationship specified',
                    'siblings': 'No sibling relationships specified',
                    'children': 'No children relationships specified'
                }
            }

    def _get_folder_context(self, folder_path: str, files: list, subfolders: list,
                          mission_content: str) -> dict:
        """
        Get folder purpose and relationships using GPT with caching.
        """
        try:
            self.logger.debug(f"Getting folder context for: {folder_path}")
            
            if not folder_path:
                raise ValueError("folder_path cannot be empty")
                
            # Ensure we have absolute path
            abs_path = os.path.abspath(folder_path)
            
            # Initialize context with absolute path
            context = {
                'path': abs_path,  # Always include the absolute path
                'purpose': '',
                'relationships': {
                    'parent': 'No parent relationship specified',
                    'siblings': 'No sibling relationships specified', 
                    'children': 'No children relationships specified'
                }
            }
            
            self.logger.debug(f"Initial context with path: {context}")
            
            # Convert to relative path for prompts and logging
            rel_path = os.path.relpath(folder_path, self.project_root)
            
            # Create prompt using relative path
            prompt = self._create_folder_context_prompt(rel_path, files, subfolders, mission_content)
            
            # Log the prompt at debug level
            self.logger.debug(f"\n🔍 FOLDER CONTEXT PROMPT for {rel_path}:\n{prompt}")
            
            # Make API call with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    client = openai.OpenAI()
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a technical architect analyzing project structure. Always respond in the exact format requested."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=500,
                        presence_penalty=-0.5,
                        frequency_penalty=0.0
                    )
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    self.logger.warning(f"API call failed, attempt {attempt + 1}/{max_retries}: {str(e)}")
                    time.sleep(2 ** attempt)  # Exponential backoff
            
            # Log the response at debug level
            content = response.choices[0].message.content.strip()
            self.logger.debug(f"\n✨ FOLDER CONTEXT RESPONSE:\n{content}")
            
            # Parse response but preserve the path
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('Purpose:'):
                    context['purpose'] = line.replace('Purpose:', '').strip()
                elif line.startswith('Parent:'):
                    context['relationships']['parent'] = line.replace('Parent:', '').strip()
                elif line.startswith('Siblings:'):
                    context['relationships']['siblings'] = line.replace('Siblings:', '').strip()
                elif line.startswith('Children:'):
                    context['relationships']['children'] = line.replace('Children:', '').strip()
                    
            self.logger.debug(f"Final context with path: {context}")
            
            # Set default purpose if none provided
            if not context['purpose']:
                context['purpose'] = f"Storage folder for {os.path.basename(abs_path)} content"
                
            # Verify path is still present
            if 'path' not in context:
                self.logger.error(f"Path missing from context after GPT response")
                context['path'] = abs_path
                
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get folder context for {folder_path}: {str(e)}")
            raise

    def _analyze_files_batch(self, folder_path: str, files: list) -> list:
        """
        Analyze all files in a folder in a single batch.
        
        Args:
            folder_path (str): Path to folder containing files
            files (list): List of filenames to analyze
            
        Returns:
            list: List of file analyses with role and description
        """
        try:
            if not files:
                return []

            client = openai.OpenAI()
            prompt = self._create_folder_analysis_prompt(folder_path, files)
            
            # Log the prompt at debug level
            self.logger.debug(f"\n🔍 FOLDER FILES ANALYSIS PROMPT:\n{prompt}")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a technical analyst identifying file roles and purposes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Log the response at debug level
            content = response.choices[0].message.content
            self.logger.debug(f"\n✨ FOLDER FILES ANALYSIS RESPONSE:\n{content}")
            
            # Parse response into file analyses
            analyses = []
            current_file = None
            
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('- **'):
                    # Extract filename and role from line like:
                    # - **├─ ./filename.ext** (CATEGORY EMOJI)
                    parts = line.split('**')
                    if len(parts) >= 3:
                        file_info = parts[1].split(' ')[-1]  # Get just the filename
                        role_part = parts[2].strip()[1:-1]  # Remove parentheses
                        current_file = {
                            'name': os.path.basename(file_info),
                            'role': role_part,
                            'description': ''
                        }
                elif line.startswith('  _') and current_file:
                    # Extract description from line like:
                    #   _Description text._
                    current_file['description'] = line.strip(' _.')
                    analyses.append(current_file)
                    current_file = None
            
            return analyses
            
        except Exception as e:
            self.logger.error(f"Failed to analyze files in {folder_path}: {str(e)}")
            raise

    def _generate_map_content(self, hierarchy: dict) -> str:
        """Generate map content from folder hierarchy with improved tree formatting."""
        def _format_folder(folder_data: dict, level: int = 0, path_prefix: str = "") -> str:
            indent = "  " * level
            content = []
            
            # Always use display_path or convert absolute to relative if needed
            folder_path = folder_data.get('display_path')
            if not folder_path and 'path' in folder_data:
                folder_path = os.path.relpath(folder_data['path'], self.project_root)

            # Create tree branch prefix
            if level > 0:
                branch = "├─ " if path_prefix else "└─ "
                full_path = f"{path_prefix}{branch}{os.path.basename(folder_path)}"
            else:
                full_path = "."  # Root folder
                
            # Add folder header with full path
            content.append(f"{indent}## {full_path}")
            content.append(f"{indent}**Purpose:** {folder_data['purpose']}\n")
            
            # Add files with better formatting and tree structure
            if folder_data.get('files'):
                content.append(f"{indent}### Files:")
                for i, file in enumerate(folder_data['files']):
                    # Use tree branches for files too
                    file_branch = "├─ " if i < len(folder_data['files']) - 1 else "└─ "
                    file_path = f"{full_path}/{file['name']}"
                    content.append(f"{indent}- **{file_branch}{file_path}** ({file['role']})  ")
                    content.append(f"{indent}  _{file['description']}_\n")
        
            # Add relationships if not root
            if level > 0:
                content.append(f"{indent}Relationships:")
                content.append(f"{indent}- **Parent:** _{folder_data['relationships']['parent']}_")
                content.append(f"{indent}- **Siblings:** _{folder_data['relationships']['siblings']}_")
                if folder_data.get('subfolders'):
                    content.append(f"{indent}- **Children:** _{folder_data['relationships']['children']}_")
        
            # Add line break before subfolders
            if folder_data.get('subfolders'):
                content.append("")
        
            # Calculate new path prefix for subfolders
            new_prefix = f"{path_prefix}{'│  ' if path_prefix else '   '}" if level > 0 else ""
        
            # Recursively add subfolders
            subfolder_items = list(folder_data.get('subfolders', {}).items())
            for i, (subfolder_name, subfolder_data) in enumerate(subfolder_items):
                is_last = (i == len(subfolder_items) - 1)
                if is_last:
                    content.append("\n" + _format_folder(subfolder_data, level + 1, new_prefix))
                else:
                    content.append("\n" + _format_folder(subfolder_data, level + 1, new_prefix))
                
            return "\n".join(content)
        
        return "# Project Map\n\n" + _format_folder(hierarchy)
    def _create_folder_context_prompt(self, folder_path: str, files: list, subfolders: list, mission_content: str) -> str:
        """Create prompt for analyzing folder context."""
        # Ensure we're using relative path
        if os.path.isabs(folder_path):
            folder_path = os.path.relpath(folder_path, self.project_root)
            
        # Build tree structure including both files and subfolders
        tree = ["📂 ./"]
        
        # Add files first
        for i, f in enumerate(files):
            prefix = "├─ " if (i < len(files) - 1 or subfolders) else "└─ "
            tree.append(f"   {prefix}{f}")
            
        # Add subfolders
        for i, d in enumerate(subfolders):
            prefix = "├─ " if i < len(subfolders) - 1 else "└─ "
            tree.append(f"   {prefix}{d}/")
        
        tree_str = "\n".join(tree)

        return f"""# Objective
Define folder's purpose and relationships:

# Current Folder Structure
{tree_str}

# Mission Context
````
{mission_content}
````

# Instructions
Provide in this format:
Purpose: 📁 [Action verb + direct object, max 10 words]
Parent: 🔼 [Direct relationship statement]
Siblings: 🔄 [Direct relationship statement]
Children: 🔽 [Direct relationship statement]

Rules:
- Start Purpose with action verb
- Use declarative statements
- Omit conditionals
- Maximum 10 words per line
- Focus on concrete actions
- Include emojis as shown in format"""
    def _format_files_content(self, files_content: dict) -> str:
        """
        Format files content for prompt with intelligent truncation.
        
        Args:
            files_content (dict): Dictionary of filename to content
            
        Returns:
            str: Formatted content string
        """
        formatted = []
        for filename, content in files_content.items():
            # Determine file type
            file_type = self._detect_file_type(filename)
            
            # Get appropriate truncation length based on file type
            max_length = self._get_max_length(file_type)
            
            # Intelligent truncation
            if len(content) > max_length:
                # Keep important sections based on file type
                truncated = self._smart_truncate(content, max_length, file_type)
                content = truncated + f"\n...[truncated, full length: {len(content)} chars]"
                
            formatted.append(f"## {filename} ({file_type})\n```\n{content}\n```")
            
        return "\n\n".join(formatted)
        
    def _detect_file_type(self, filename: str) -> str:
        """Detect file type based on extension and content patterns."""
        ext = os.path.splitext(filename)[1].lower()
        
        # Common file types
        type_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.html': 'HTML',
            '.css': 'CSS',
            '.md': 'Markdown',
            '.json': 'JSON',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.xml': 'XML',
            '.sql': 'SQL',
            '.sh': 'Shell',
            '.bat': 'Batch',
            '.ps1': 'PowerShell',
            '.txt': 'Text'
        }
        
        return type_map.get(ext, 'Unknown')
        
    def _get_max_length(self, file_type: str) -> int:
        """Get appropriate max length based on file type."""
        # Customize lengths based on file type importance
        type_lengths = {
            'Python': 2000,    # More context for code
            'JavaScript': 2000,
            'TypeScript': 2000,
            'HTML': 1500,
            'CSS': 1000,
            'Markdown': 3000,  # More context for documentation
            'JSON': 1000,
            'YAML': 1000,
            'XML': 1000,
            'SQL': 1500,
            'Shell': 1000,
            'Batch': 1000,
            'PowerShell': 1000,
            'Text': 1000
        }
        
        return type_lengths.get(file_type, 1000)
        
    def _smart_truncate(self, content: str, max_length: int, file_type: str) -> str:
        """Intelligently truncate content based on file type."""
        if len(content) <= max_length:
            return content
            
        if file_type in ['Python', 'JavaScript', 'TypeScript']:
            # Keep imports/requires and main structure
            lines = content.split('\n')
            imports = [l for l in lines if l.strip().startswith(('import ', 'from ', 'require'))]
            classes = [l for l in lines if l.strip().startswith(('class ', 'def ', 'function'))]
            
            important = imports + ['...'] + classes
            important_content = '\n'.join(important)
            
            if len(important_content) < max_length:
                return important_content
                
        elif file_type == 'Markdown':
            # Keep headers and structure
            lines = content.split('\n')
            headers = [l for l in lines if l.strip().startswith('#')]
            return '\n'.join(headers[:max_length//20]) + '\n...'
            
        # Default truncation with ellipsis
        return content[:max_length-3] + '...'

    async def generate_global_map(self, mission_filepath=".aider.mission.md"):
        """
        Generate a global project map based on mission context.
        
        Args:
            mission_filepath (str): Path to mission file
            
        Raises:
            ValueError: If mission file is invalid
            Exception: For other errors during map generation
        """
        try:
            self.logger.logger.setLevel(logging.DEBUG)
            self.logger.debug("🔍 Starting global map generation")
            
            if not os.path.exists(mission_filepath):
                raise ValueError(f"Mission file not found: {mission_filepath}")
                
            # Load mission content
            with open(mission_filepath, 'r', encoding='utf-8') as f:
                mission_content = f.read()
                
            # Analyze full project structure
            self.logger.debug("📂 Analyzing project structure")
            hierarchy = self._analyze_folder_hierarchy(".", mission_content, mission_content)
            
            # Generate map content
            self.logger.debug("📝 Generating map content")
            map_content = self._generate_map_content(hierarchy)
            
            # Save to map.md
            self.logger.debug("💾 Saving global map")
            with open("map.md", 'w', encoding='utf-8') as f:
                f.write(map_content)

            # Generate visualization using VisionManager
            self.logger.debug("🎨 Generating repository visualization")
            await self._vision_manager.update_map()
                
            self.logger.success("✨ Global map generated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to generate global map: {str(e)}")
            raise

    def _get_ignore_patterns(self) -> list:
        """Get list of patterns to ignore from .gitignore and defaults."""
        patterns = [
            '.git/*',  # Ignore all .git directory contents
            '.git*',   # Keep this for .gitignore and other git files
            '.aider*',
            'node_modules',
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.DS_Store',
            'Thumbs.db'
        ]
        
        # Add patterns from .gitignore if it exists
        if os.path.exists('.gitignore'):
            try:
                with open('.gitignore', 'r', encoding='utf-8') as f:
                    patterns.extend(line.strip() for line in f 
                                  if line.strip() and not line.startswith('#'))
            except Exception as e:
                self.logger.warning(f"⚠️ Could not read .gitignore: {str(e)}")
        
        # Add patterns from .aiderignore if it exists        
        if os.path.exists('.aiderignore'):
            try:
                with open('.aiderignore', 'r', encoding='utf-8') as f:
                    patterns.extend(line.strip() for line in f 
                                  if line.strip() and not line.startswith('#'))
            except Exception as e:
                self.logger.warning(f"⚠️ Could not read .aiderignore: {str(e)}")
                
        return patterns

    def _should_ignore(self, path: str, ignore_patterns: list) -> bool:
        """Check if a path should be ignored based on ignore patterns."""
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False

    def _is_binary_file(self, file_path: str) -> bool:
        """
        Check if a file is binary by reading its first few bytes.
        
        Args:
            file_path (str): Path to file to check
            
        Returns:
            bool: True if file appears to be binary, False otherwise
        """
        try:
            # Define known text file extensions
            text_extensions = {
                '.txt', '.md', '.py', '.js', '.html', '.css', '.json', 
                '.yaml', '.yml', '.ini', '.cfg', '.conf', '.sh', '.bat',
                '.ps1', '.env', '.rst', '.xml', '.csv', '.sql', '.htaccess',
                '.gitignore', '.dockerignore', '.editorconfig', '.toml',
                '.properties', '.gradle', '.jsx', '.tsx', '.vue', '.php',
                '.rb', '.pl', '.java', '.kt', '.go', '.rs', '.c', '.cpp',
                '.h', '.hpp', '.cs', '.vb', '.swift', '.r', '.scala',
                '.clj', '.ex', '.exs', '.erl', '.fs', '.fsx', '.dart'
            }
            
            # Check extension first
            ext = os.path.splitext(file_path)[1].lower()
            if ext in text_extensions:
                return False
                
            # For unknown extensions, check content
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                
            # Check for null bytes
            if b'\x00' in chunk:
                return True
                
            # Try decoding as text
            try:
                chunk.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
                
        except Exception as e:
            self.logger.error(f"Error checking if {file_path} is binary: {str(e)}")
            return True  # Assume binary on error to be safe

    def _analyze_file(self, filename: str, folder_context: dict) -> dict:
        """
        Analyze single file's role and purpose.
        
        Args:
            filename (str): Name of file to analyze
            folder_context (dict): Context information about the containing folder
            
        Returns:
            dict: Analysis containing:
                - name: Filename
                - role: Technical role with emoji
                - description: Purpose description
        """
        try:
            # Get simple folder path from context
            folder_path = folder_context.get('path', '')
            if not folder_path:
                raise ValueError("No valid path in folder context")

            # Build simple file path by joining folder and filename
            file_path = os.path.join(folder_path, filename)
            
            client = openai.OpenAI()
            prompt = self._create_file_analysis_prompt(file_path, folder_context)
            
            # Log the prompt at debug level
            self.logger.debug(f"\n🔍 FILE ANALYSIS PROMPT for {file_path}:\n{prompt}")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a technical analyst identifying file roles and purposes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            # Log the response at debug level
            content = response.choices[0].message.content
            self.logger.debug(f"\n✨ FILE ANALYSIS RESPONSE for {file_path}:\n{content}")
            
            # Parse response into structure 
            parts = content.split(' - ', 1)
            
            return {
                'name': filename,
                'path': file_path,  # Add relative path to result
                'role': parts[0].strip(),
                'description': parts[1].strip() if len(parts) > 1 else ''
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze file {filename}: {str(e)}")
            raise

    def _parse_folder_analysis(self, analysis_text: str) -> dict:
        """
        Parse and validate GPT analysis response into structured format.
        
        Args:
            analysis_text (str): Raw GPT response text
            
        Returns:
            dict: Validated and structured analysis
            
        Raises:
            ValueError: If response format is invalid
        """
        # Initialize with required structure
        sections = {
            'purpose': '',
            'files': [],
            'relationships': {'parent': '', 'siblings': '', 'children': ''}
        }
        
        # Validate basic structure
        if not analysis_text or not isinstance(analysis_text, str):
            raise ValueError("Invalid analysis text")
            
        required_sections = ['FOLDER PURPOSE', 'FILE ANALYSIS', 'RELATIONSHIPS']
        for section in required_sections:
            if section not in analysis_text:
                raise ValueError(f"Missing required section: {section}")
        
        current_section = None
        current_file = None
        
        for line in analysis_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Section detection with validation
            if line.startswith('1. FOLDER PURPOSE'):
                current_section = 'purpose'
                if sections['purpose']:
                    raise ValueError("Duplicate FOLDER PURPOSE section")
            elif line.startswith('2. FILE ANALYSIS'):
                current_section = 'files'
            elif line.startswith('3. RELATIONSHIPS'):
                current_section = 'relationships'
                if any(sections['relationships'].values()):
                    raise ValueError("Duplicate RELATIONSHIPS section")
            
            # Content parsing with validation
            elif current_section == 'purpose' and line.startswith('-'):
                content = line[1:].strip()
                if not content:
                    continue
                sections['purpose'] += content + ' '
                
            elif current_section == 'files' and line.startswith('-'):
                # Validate and parse file entry
                try:
                    # Expected format: "- filename.ext (📊 ROLE) - description"
                    if ' - ' not in line:
                        raise ValueError(f"Invalid file entry format: {line}")
                        
                    parts = line[1:].split(' - ', 1)
                    if len(parts) != 2:
                        raise ValueError(f"Invalid file entry parts: {line}")
                        
                    name_role = parts[0].split(' (')
                    if len(name_role) != 2 or not name_role[1].endswith(')'):
                        raise ValueError(f"Invalid file role format: {parts[0]}")
                        
                    file_entry = {
                        'name': name_role[0].strip(),
                        'role': name_role[1].rstrip(')'),
                        'description': parts[1].strip()
                    }
                    
                    # Validate entry
                    if not all(file_entry.values()):
                        raise ValueError(f"Missing required file entry fields: {file_entry}")
                        
                    sections['files'].append(file_entry)
                    
                except ValueError as e:
                    self.logger.warning(f"Skipping invalid file entry: {str(e)}")
                    continue
                    
            elif current_section == 'relationships':
                try:
                    if line.startswith('- Parent:'):
                        sections['relationships']['parent'] = line.split(':', 1)[1].strip()
                    elif line.startswith('- Siblings:'):
                        sections['relationships']['siblings'] = line.split(':', 1)[1].strip()
                    elif line.startswith('- Children:'):
                        sections['relationships']['children'] = line.split(':', 1)[1].strip()
                except IndexError:
                    self.logger.warning(f"Invalid relationship line format: {line}")
                    continue
        
        # Final validation
        if not sections['purpose']:
            raise ValueError("Empty folder purpose")
            
        if not any(sections['relationships'].values()):
            raise ValueError("No relationships defined")
            
        return sections
    async def update_folder(self, folder_path: str):
        """
        Updates analysis of a specific folder and regenerates SVG.
        
        Args:
            folder_path (str): Path to modified folder
        """
        try:
            if not self._initial_mapping_in_progress:
                self.logger.debug(f"🔄 Updating folder analysis for: {folder_path}")
                
                # Update folder analysis
                mission_content = self._get_mission_content()
                objective_content = self._get_objective_content()
                
                # Analyze only the modified folder
                folder_analysis = self._analyze_folder_level(
                    folder_path=folder_path,
                    files_content=self._get_folder_files_content(folder_path),
                    subfolders=self._get_subfolders(folder_path),
                    mission_content=mission_content,
                    objective_content=objective_content
                )
                
                # Update repo map
                await self._vision_manager.update_map()
                
                self.logger.debug(f"✨ Folder analysis and visualization updated for: {folder_path}")
                
                return folder_analysis
                
        except Exception as e:
            self.logger.error(f"Failed to update folder analysis: {str(e)}")
            raise
    def _create_folder_analysis_prompt(self, folder_path: str, files: list) -> str:
        """Create prompt for analyzing all files in a folder."""
        # Get absolute and relative paths
        abs_path = os.path.abspath(folder_path)
        rel_path = os.path.relpath(folder_path, self.project_root)
        
        # Get ignore patterns
        ignore_patterns = self._get_ignore_patterns()
        
        # Filter files using ignore patterns
        files = [f for f in files if not self._should_ignore(os.path.join(rel_path, f), ignore_patterns)]
        
        # Get subfolders
        subfolders = self._get_subfolders(folder_path)
        
        tree = []
        
        # Handle root folder differently
        if rel_path == "." or abs_path == self.project_root:
            tree.append("📂 ./")
            # Add current folder files (filtered)
            for i, f in enumerate(files):
                prefix = "├─" if (i < len(files) - 1 or subfolders) else "└─"
                tree.append(f"   {prefix} {f}")
            
            # Add subfolders
            for i, d in enumerate(subfolders):
                prefix = "├─" if i < len(subfolders) - 1 else "└─"
                tree.append(f"   {prefix} {d}/")
        else:
            # For subfolders, show parent path and filtered siblings
            parent_path = os.path.dirname(abs_path)
            
            # Add path from root (filtered)
            parts = rel_path.split(os.sep)
            for i, part in enumerate(parts[:-1]):
                prefix = "   " * i
                tree.append(f"{prefix}├─ {part}/")
            
            # Add current folder
            current_prefix = "   " * (len(parts) - 1)
            tree.append(f"{current_prefix}📂 {os.path.basename(folder_path)}/")
            
            # Add current folder files (filtered)
            file_prefix = "   " * len(parts)
            for i, f in enumerate(files):
                prefix = "├─" if i < len(files) - 1 else "└─"
                tree.append(f"{file_prefix}{prefix} {f}")
            
            # Add filtered sibling folders
            if parent_path:
                siblings = []
                for sibling in sorted(os.listdir(parent_path)):
                    sibling_path = os.path.join(parent_path, sibling)
                    rel_sibling = os.path.relpath(sibling_path, self.project_root)
                    
                    # Skip if should be ignored
                    if self._should_ignore(rel_sibling, ignore_patterns):
                        continue
                        
                    if os.path.isdir(sibling_path) and sibling_path != abs_path:
                        siblings.append(sibling)
                        
                # Add filtered siblings with their first few contents
                for i, sibling in enumerate(siblings):
                    is_last = (i == len(siblings) - 1)
                    sibling_path = os.path.join(parent_path, sibling)
                    tree.append(f"{current_prefix}{'└─' if is_last else '├─'} {sibling}/")
                    
                    # Add first few contents of sibling (also filtered)
                    try:
                        sibling_contents = [
                            item for item in sorted(os.listdir(sibling_path))
                            if not self._should_ignore(os.path.join(rel_sibling, item), ignore_patterns)
                        ][:3]  # Limit to first 3 non-ignored items
                        
                        for j, item in enumerate(sibling_contents):
                            is_last_item = (j == len(sibling_contents) - 1)
                            tree.append(f"{file_prefix}{'└─' if is_last_item else '├─'} {item}")
                            
                        if len(sibling_contents) > 3:
                            tree.append(f"{file_prefix}└─ ...")
                    except OSError:
                        continue

        tree_str = "\n".join(tree)

        return f"""#Objective
Analyze all files in this folder structure:

# Project Structure
{tree_str}

# Current Folder
{rel_path}

# Instructions
Generate descriptions in this EXACT format:
### Files:
- **[tree prefix] [relative path]** ([CATEGORY] [EMOJI])  
  _[Action verb] [dense technical description] | USE: [when to use]; NOT [when not to use]._

Categories (select ONE per file):
Core Project Files:
* PRIMARY (📊) - Final outputs, key results
* SPECIFICATION (📋) - Requirements, standards
* IMPLEMENTATION (⚙️) - Core functionality
* DOCUMENTATION (📚) - Explanations, guides

Support Files:
* CONFIGURATION (⚡) - Settings, parameters
* UTILITY (🛠️) - Helper functions, tools
* TEST (🧪) - Validation, verification
* BUILD (📦) - Compilation, deployment

Working Files:
* WORK DOCUMENT (✍️) - Active development
* DRAFT (📝) - Work in progress
* TEMPLATE (📄) - Patterns, structures
* ARCHIVE (📂) - Historical records

Data Files:
* SOURCE DATA (💾) - Input data
* GENERATED (⚡) - Computed results
* CACHE (💫) - Temporary storage
* BACKUP (💿) - Data preservation

Rules for each description:
- Start with precise action verb
- Pack technical details densely
- Include key parameters/patterns
- Specify input/output formats
- State dependencies if any
- Add clear usage guidance
- Mention critical constraints
- Note performance impacts

Example:
- **├─ ./analysis_results.md** (📊 PRIMARY)  
  _Aggregates biomarker correlation matrices (r>0.7) using sliding window analysis (window=30d) for 5 key protein markers | USE: When validating longitudinal marker patterns; NOT for preliminary screening or single-timepoint data._

Remember:
- Technical precision over general descriptions
- Include quantitative parameters when relevant
- State specific conditions and constraints
- Highlight unique technical aspects"""
