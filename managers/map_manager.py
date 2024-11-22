import os
import asyncio
import logging
import time
import fnmatch
from pathlib import Path
import fnmatch
from utils.logger import Logger
import openai
import tiktoken
from dotenv import load_dotenv

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
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        self.api_semaphore = asyncio.Semaphore(10)
    def _analyze_folder_level(self, folder_path: str, files_content: dict, 
                            subfolders: list, mission_content: str, 
                            objective_content: str) -> dict:
        """
        Analyze a single folder level with its files and immediate subfolders.
        
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
        if not folder_path:
            raise ValueError("folder_path cannot be empty")
            
        if not isinstance(files_content, dict):
            raise TypeError("files_content must be a dictionary")
            
        if not isinstance(subfolders, list):
            raise TypeError("subfolders must be a list")
            
        try:
            # Validate folder exists
            if not os.path.exists(folder_path):
                raise ValueError(f"Folder does not exist: {folder_path}")
                
            if not os.path.isdir(folder_path):
                raise ValueError(f"Path is not a directory: {folder_path}")
            
            # Get folder context including purpose and relationships
            folder_context = self._get_folder_context(
                folder_path=folder_path,
                files=list(files_content.keys()),
                subfolders=subfolders,
                mission_content=mission_content
            )
            
            # Analyze each file in the folder
            analyzed_files = []
            for filename, content in files_content.items():
                try:
                    if not isinstance(content, str):
                        raise TypeError(f"Content for {filename} must be string")
                        
                    file_analysis = self._analyze_file(filename, folder_context)
                    analyzed_files.append(file_analysis)
                    
                except Exception as e:
                    self.logger.warning(
                        f"Failed to analyze file {filename}: {str(e)}\n"
                        f"Error type: {type(e).__name__}"
                    )
                    analyzed_files.append({
                        'name': filename,
                        'role': '⚠️ ERROR',
                        'description': f'Analysis failed: {str(e)}'
                    })
            
            # Validate folder context
            if not folder_context.get('purpose'):
                raise ValueError(f"Failed to determine purpose for {folder_path}")
                
            if not folder_context.get('relationships'):
                raise ValueError(f"Failed to determine relationships for {folder_path}")
            
            return {
                'path': folder_path,
                'purpose': folder_context['purpose'],
                'files': analyzed_files,
                'relationships': folder_context['relationships']
            }
            
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
        # Validate and normalize path
        if not folder_path:
            raise ValueError("folder_path cannot be empty")
            
        # Convert to absolute path if relative
        folder_path = os.path.abspath(folder_path)
            
        if not os.path.exists(folder_path):
            raise ValueError(f"Folder does not exist: {folder_path}")
            
        if not os.path.isdir(folder_path):
            raise ValueError(f"Path is not a directory: {folder_path}")
            
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

            return folder_analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze folder hierarchy for {folder_path}: {str(e)}")
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

    def _create_folder_context_prompt(self, folder_path: str, files: list, 
                                    subfolders: list, mission_content: str, 
                                    objective_content: str) -> str:
        """
        Create prompt for analyzing folder context.
        
        Args:
            folder_path (str): Path to current folder
            files (list): List of files in folder
            subfolders (list): List of subfolders
            mission_content (str): Overall mission context
            objective_content (str): Current objective context
            
        Returns:
            str: Formatted prompt for GPT analysis
        """
        return f"""Analyze this folder's purpose and relationships:

Current Folder: {folder_path}

Files Present:
{chr(10).join(f'- {f}' for f in files)}

Subfolders:
{chr(10).join(f'- {f}' for f in subfolders)}

Mission Context:
{mission_content}

Current Objective:
{objective_content}

Analyze and provide:
1. FOLDER PURPOSE
   - Main purpose of this folder
   - How it supports the mission
   - Why files are grouped here

2. FILE ANALYSIS
   - Role of each file
   - How files work together
   - Critical vs. supporting files

3. RELATIONSHIPS
   - Parent: How this connects to parent folder
   - Siblings: Relationship with peer folders
   - Children: Purpose of subfolders

Format response with these exact headers:
Purpose: [folder purpose]
Parent: [parent relationship]
Siblings: [sibling relationships]
Children: [children relationships]"""

    def _get_folder_context(self, folder_path: str, files: list, subfolders: list,
                          mission_content: str) -> dict:
        """
        Get folder purpose and relationships using GPT with caching.
        
        Args:
            folder_path (str): Path to current folder
            files (list): List of files in folder
            subfolders (list): List of subfolders
            mission_content (str): Overall mission context
            objective_content (str): Current objective context
            
        Returns:
            dict: Folder context including purpose and relationships
            
        Raises:
            ValueError: If input parameters are invalid
            Exception: For API or parsing errors
        """
        if not folder_path:
            raise ValueError("folder_path cannot be empty")
            
        try:
            # Generate cache key
            cache_key = f"{folder_path}:{','.join(sorted(files))}:{','.join(sorted(subfolders))}"
            
            # Check cache first
            if hasattr(self, '_context_cache'):
                cached = self._context_cache.get(cache_key)
                if cached:
                    self.logger.debug(f"Using cached context for {folder_path}")
                    return cached
            else:
                # Initialize cache if needed
                self._context_cache = {}
            
            client = openai.OpenAI()
            
            # Improved prompt for more structured response
            prompt = f"""Analyze this folder's purpose and relationships:

Current Folder: {folder_path}

Files Present:
{chr(10).join(f'- {f}' for f in files)}

Subfolders:
{chr(10).join(f'- {f}' for f in subfolders)}

Mission Context:
{mission_content}

Please provide your analysis in this EXACT format:
Purpose: [One line describing the main purpose of this folder]
Parent: [How this folder relates to its parent]
Siblings: [How this folder relates to peer folders]
Children: [How this folder relates to its subfolders]

Important:
- Each section MUST start with the exact label (Purpose:, Parent:, etc.)
- The Purpose section is REQUIRED and must be meaningful
- Keep each section to 1-2 lines maximum
- Use clear, concise language"""

            # Make API call with retry logic and improved parameters
            max_retries = 3
            for attempt in range(max_retries):
                try:
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
            
            # Parse response with improved error handling
            content = response.choices[0].message.content.strip()
            self.logger.debug(f"GPT Response for {folder_path}:\n{content}")
            
            # Initialize context with default values
            context = {
                'purpose': '',
                'relationships': {
                    'parent': 'No parent relationship specified',
                    'siblings': 'No sibling relationships specified',
                    'children': 'No children relationships specified'
                }
            }
            
            # Parse response line by line with more robustness
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue

                # More flexible parsing approach
                for key in ['Purpose:', 'Parent:', 'Siblings:', 'Children:']:
                    if line.startswith(key):
                        value = line[len(key):].strip()
                        if key == 'Purpose:':
                            context['purpose'] = value
                        else:
                            rel_key = key.lower().rstrip(':')
                            context['relationships'][rel_key] = value
            
            # Enhanced validation with fallback
            if not context['purpose']:
                folder_name = os.path.basename(folder_path)
                context['purpose'] = f"Storage folder for {folder_name} related content"
                self.logger.warning(f"Generated default purpose for {folder_path}: {context['purpose']}")
            
            # Cache the result
            self._context_cache[cache_key] = context
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get folder context for {folder_path}: {str(e)}")
            raise

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
            client = openai.OpenAI()
            prompt = self._create_file_analysis_prompt(filename, folder_context)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a technical analyst identifying file roles and purposes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            # Parse response into structure
            content = response.choices[0].message.content
            parts = content.split(' - ', 1)
            
            return {
                'name': filename,
                'role': parts[0].strip(),
                'description': parts[1].strip() if len(parts) > 1 else ''
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze file {filename}: {str(e)}")
            raise

    def _generate_map_content(self, hierarchy: dict) -> str:
        """
        Generate map content from folder hierarchy.
        """
        def _format_folder(folder_data: dict, level: int = 0) -> str:
            indent = "  " * level
            content = []
            
            # Add folder header and purpose
            content.append(f"{indent}## {folder_data['path']}")
            content.append(f"{indent}Purpose: {folder_data['purpose']}\n")
            
            # Add files
            for file in folder_data['files']:
                content.append(f"{indent}- {file['name']} ({file['role']}) - {file['description']}")
            
            # Add relationships if not root
            if level > 0:
                content.append(f"\n{indent}Relationships:")
                content.append(f"{indent}- Parent: {folder_data['relationships']['parent']}")
                content.append(f"{indent}- Siblings: {folder_data['relationships']['siblings']}")
                if folder_data['subfolders']:
                    content.append(f"{indent}- Children: {folder_data['relationships']['children']}")
            
            # Recursively add subfolders
            for subfolder_name, subfolder_data in folder_data['subfolders'].items():
                content.append("\n" + _format_folder(subfolder_data, level + 1))
                
            return "\n".join(content)
        
        return "# Project Map\n\n" + _format_folder(hierarchy)
    def _create_file_analysis_prompt(self, filename: str, folder_context: dict) -> str:
        """Create prompt for analyzing a single file's role."""
        return f"""Analyze this file's role in its folder:

Filename: {filename}
Folder Purpose: {folder_context['purpose']}

Determine the file's:
1. Technical role (using emoji categories below)
2. Specific purpose in this folder
3. How it supports the folder's purpose

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
* BACKUP (💿) - System backups

Return in format:
[EMOJI ROLE] - [Purpose description]"""
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

    def generate_global_map(self, mission_filepath=".aider.mission.md"):
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
                
            self.logger.success("✨ Global map generated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to generate global map: {str(e)}")
            raise

    def _get_ignore_patterns(self) -> list:
        """Get list of patterns to ignore from .gitignore and defaults."""
        patterns = [
            '.git*',
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
