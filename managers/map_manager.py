import os
import asyncio
import logging
import time
from pathlib import Path
from utils.fs_utils import FSUtils
from utils.logger import Logger
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
        self.fs_utils = FSUtils()
        self.project_root = os.path.abspath('.')  # Store absolute path of project root
        self._initial_mapping_in_progress = False
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
        """
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
                
            # Get folder context which now includes file analysis
            folder_context = self._get_folder_context(
                folder_path=abs_folder_path,
                files=list(files_content.keys()),
                subfolders=subfolders,
                mission_content=mission_content
            )
            
            self.logger.debug(f"Folder context: {folder_context}")
            
            # Validate and build result
            if not folder_context.get('purpose'):
                raise ValueError(f"Failed to determine purpose for {folder_path}")
            
            analysis_result = {
                'path': abs_folder_path,
                'purpose': folder_context['purpose'],
                'files': folder_context.get('files', []),  # File analysis now comes from folder context
                'relationships': folder_context.get('relationships', {}),
                'structure': {
                    'path': abs_folder_path,
                    'files': list(files_content.keys()),
                    'subfolders': subfolders,
                    'mission_context': mission_content
                }
            }
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
        """Analyze folder hierarchy using a two-phase approach."""
        try:
            self._initial_mapping_in_progress = True
            folder_path = os.path.abspath(folder_path)
            
            if not folder_path:
                raise ValueError("folder_path cannot be empty")
            
            if not os.path.exists(folder_path):
                raise ValueError(f"Folder does not exist: {folder_path}")
                
            if not os.path.isdir(folder_path):
                raise ValueError(f"Path is not a directory: {folder_path}")
            
            # Phase 1: Analyze top two levels together
            top_level_analysis = self._analyze_top_levels(
                folder_path=folder_path,
                mission_content=mission_content,
                max_depth=2
            )
            
            # Phase 2: For each level-2 folder, analyze its complete subtree
            for subfolder_name, subfolder_data in top_level_analysis.get('subfolders', {}).items():
                subfolder_path = os.path.join(folder_path, subfolder_name)
                subtree_analysis = self._analyze_complete_subtree(
                    folder_path=subfolder_path,
                    mission_content=mission_content
                )
                # Update the subfolder data with complete subtree analysis
                top_level_analysis['subfolders'][subfolder_name].update(subtree_analysis)
                
        except Exception as e:
            self.logger.error(f"Failed to validate folder path: {str(e)}")
            self._initial_mapping_in_progress = False  # Reset on error
            raise
            
        try:
            # Once complete analysis is done, generate SVG
            if folder_path == "." and self._initial_mapping_in_progress:
                self._initial_mapping_in_progress = False
                asyncio.run(self._vision_manager.update_map())

            return top_level_analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze folder hierarchy for {folder_path}: {str(e)}")
            self._initial_mapping_in_progress = False  # Reset on error
            raise



    def _create_folder_context_prompt(self, folder_path: str, files: list, subfolders: list, mission_content: str) -> str:
        """Create prompt for analyzing folder and all its files at once."""
        # Set current folder for tree building
        self.fs_utils.set_current_folder(os.path.abspath(folder_path))
        
        # Build tree structure using FSUtils
        tree = self.fs_utils.build_tree_structure(
            current_path=".",
            files=files,
            subfolders=subfolders,
            max_depth=3  # Show 3 levels for non-current branches
        )
        
        # Join tree lines
        tree_str = "\n".join(tree)

        return f"""# Objective
Analyze this folder and its files:

# Current Structure
👉 {tree_str}

# Mission Context
````
{mission_content}
````

# Instructions
Provide analysis in this format:

Folder: 📁 [Action verb + direct object, max 10 words]

Files:
- **[tree prefix] [filename]** ([CATEGORY] [EMOJI])
  _[Action verb] [technical description]_

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
* ARCHIVE (🗄️) - Historical records

Data Files:
* SOURCE DATA (💾) - Input data
* GENERATED (⚡) - Computed results  
* CACHE (💫) - Temporary storage
* BACKUP (💿) - Data preservation

Rules:
- Start all descriptions with action verb
- Use technical, specific language
- Maximum 10 words per line
- Include appropriate emojis"""

    def _analyze_top_levels(self, folder_path: str, mission_content: str, max_depth: int = 2) -> dict:
        """Analyze top levels of folder structure in one go."""
        try:
            # Collect all files and folders up to max_depth
            structure = self._collect_structure(folder_path, max_depth)
            
            # Create comprehensive prompt for top levels
            prompt = self._create_multilevel_analysis_prompt(
                structure=structure,
                mission_content=mission_content
            )
            
            # Get analysis from LLM
            analysis = self._get_llm_analysis(prompt)
            
            return self._parse_multilevel_analysis(analysis, structure)
            
        except Exception as e:
            self.logger.error(f"Failed to analyze top levels: {str(e)}")
            raise

    def _analyze_complete_subtree(self, folder_path: str, mission_content: str) -> dict:
        """Analyze complete subtree of a folder in one go."""
        try:
            # Collect complete subtree structure
            structure = self._collect_structure(folder_path, max_depth=None)
            
            # Create prompt for complete subtree analysis
            prompt = self._create_subtree_analysis_prompt(
                structure=structure,
                mission_content=mission_content
            )
            
            # Get analysis from LLM
            analysis = self._get_llm_analysis(prompt)
            
            return self._parse_multilevel_analysis(analysis, structure)
            
        except Exception as e:
            self.logger.error(f"Failed to analyze subtree: {str(e)}")
            raise

    def _collect_structure(self, folder_path: str, max_depth: int = None, current_depth: int = 0) -> dict:
        """Collect folder structure up to specified depth."""
        structure = {
            'path': folder_path,
            'files': self.fs_utils.get_folder_files(folder_path),
            'subfolders': {}
        }
        
        if max_depth is None or current_depth < max_depth:
            for subfolder in self.fs_utils.get_subfolders(folder_path):
                subfolder_path = os.path.join(folder_path, subfolder)
                structure['subfolders'][subfolder] = self._collect_structure(
                    subfolder_path, 
                    max_depth,
                    current_depth + 1
                )
                
        return structure

    def _create_multilevel_analysis_prompt(self, structure: dict, mission_content: str) -> str:
        """Create prompt for analyzing multiple levels at once."""
        return f"""Analyze this complete folder structure and all its files:

# Current Structure
{self._format_structure_for_prompt(structure)}

# Mission Context
{mission_content}

# Instructions
Provide a complete analysis in this format:

## Root Folder
Purpose: [Action verb + direct object, max 10 words]

Files:
- **[filename]** ([CATEGORY] [EMOJI])
  _[Action verb] [technical description]_

## Subfolders
For each subfolder:
- Purpose: [Action verb + direct object]
- Files analysis (same format as above)
- Relationships with other folders

Use these categories:
Core: PRIMARY 📊, SPEC 📋, IMPL ⚙️, DOCS 📚
Support: CONFIG ⚡, UTIL 🛠️, TEST 🧪, BUILD 📦
Working: WORK ✍️, DRAFT 📝, TEMPLATE 📄, ARCHIVE 📂
Data: SOURCE 💾, GEN ⚡, CACHE 💫, BACKUP 💿"""

    def _create_subtree_analysis_prompt(self, structure: dict, mission_content: str) -> str:
        """Create prompt for analyzing a complete subtree."""
        return f"""Analyze this complete subtree structure and ALL its files:

# Current Structure
{self._format_structure_for_prompt(structure)}

# Mission Context
{mission_content}

# Instructions
Provide a complete analysis of the entire subtree:

## Current Folder
Purpose: [Action verb + direct object, max 10 words]

Files:
- **[filename]** ([CATEGORY] [EMOJI])
  _[Action verb] [technical description]_

## Complete Subtree Analysis
For each subfolder (all levels):
- Full path and purpose
- Complete file analysis
- Technical relationships
- Dependencies and data flow

Use same categories as before."""

    def _format_structure_for_prompt(self, structure: dict, indent: str = "") -> str:
        """Format folder structure for prompt display."""
        lines = []
        
        # Add current folder
        folder_name = os.path.basename(structure['path']) or '.'
        lines.append(f"{indent}📂 {folder_name}/")
        
        # Add files
        for file in structure['files']:
            lines.append(f"{indent}├── {file}")
            
        # Add subfolders
        for name, subfolder in structure['subfolders'].items():
            lines.append(self._format_structure_for_prompt(subfolder, indent + "│   "))
            
        return "\n".join(lines)

    def _get_llm_analysis(self, prompt: str) -> str:
        """Get analysis from LLM."""
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a technical architect analyzing project structure. Always respond in the exact format requested."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"LLM analysis failed: {str(e)}")
            raise

    def _parse_multilevel_analysis(self, analysis: str, structure: dict) -> dict:
        """Parse the multilevel analysis response into structured data."""
        result = {
            'path': structure['path'],
            'purpose': '',
            'files': [],
            'subfolders': {},
            'relationships': {}
        }
        
        current_section = None
        current_folder = None
        
        for line in analysis.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('## Root Folder') or line.startswith('## Current Folder'):
                current_section = 'root'
                current_folder = result
            elif line.startswith('Purpose:'):
                if current_folder:
                    current_folder['purpose'] = line.replace('Purpose:', '').strip()
            elif line.startswith('- **') and '**' in line:
                if current_folder:
                    file_info = self._parse_file_line(line)
                    if file_info:
                        current_folder['files'].append(file_info)
            elif line.startswith('## Subfolders'):
                current_section = 'subfolders'
            elif line.startswith('## Complete Subtree Analysis'):
                current_section = 'subtree'
            elif line.startswith('- Full path:'):
                path = line.replace('- Full path:', '').strip()
                current_folder = result['subfolders'].setdefault(path, {
                    'path': path,
                    'purpose': '',
                    'files': [],
                    'relationships': {}
                })
                
        return result

    def _parse_file_line(self, line: str) -> dict:
        """Parse a file analysis line into structured data."""
        try:
            # Extract filename and role
            name_part = line.split('**')[1]
            role_part = line.split('(')[1].split(')')[0]
            
            # Extract description if present
            description = ''
            if '_' in line:
                description = line.split('_')[1].strip()
                
            return {
                'name': name_part.strip(),
                'role': role_part.strip(),
                'description': description
            }
        except Exception:
            return None

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
            files = self.fs_utils.get_folder_files(abs_path)
            subfolders = self.fs_utils.get_subfolders(abs_path)
            
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
        Get folder purpose and relationships using GPT.
        
        Args:
            folder_path (str): Path to current folder
            files (list): List of files in folder
            subfolders (list): List of subfolders
            mission_content (str): Overall mission context
            
        Returns:
            dict: Folder context including purpose and relationships
            
        Raises:
            ValueError: If folder_path is empty or invalid
            Exception: For API or parsing errors
        """
        try:
            self.logger.debug(f"Getting folder context for: {folder_path}")
            
            if not folder_path:
                raise ValueError("folder_path cannot be empty")
                
            # Ensure we have absolute path
            abs_path = os.path.abspath(folder_path)
            
            # Initialize context with absolute path
            context = {
                'path': abs_path,
                'purpose': '',
                'relationships': {
                    'parent': 'No parent relationship specified',
                    'siblings': 'No sibling relationships specified', 
                    'children': 'No children relationships specified'
                }
            }
            
            # Create prompt using relative path
            rel_path = os.path.relpath(folder_path, self.project_root)
            prompt = self._create_folder_context_prompt(rel_path, files, subfolders, mission_content)
            
            # Log the prompt at debug level
            self.logger.debug(f"\n🔍 FOLDER CONTEXT PROMPT for {rel_path}:\n{prompt}")
            
            # Make API call
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a technical architect analyzing project structure. Always respond in the exact format requested."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Log the response at debug level
            content = response.choices[0].message.content.strip()
            self.logger.debug(f"\n✨ FOLDER CONTEXT RESPONSE:\n{content}")
            
            # Parse response
            current_file = None
            files_analysis = []
            
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('Folder:'):
                    context['purpose'] = line.replace('Folder:', '').strip()
                elif line.startswith('- **'):
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
                    files_analysis.append(current_file)
                    current_file = None
                    
            # Add files analysis to context
            context['files'] = files_analysis
                    
            self.logger.debug(f"Final context with path: {context}")
            
            # Set default purpose if none provided
            if not context['purpose']:
                context['purpose'] = f"Storage folder for {os.path.basename(abs_path)} content"
                
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get folder context for {folder_path}: {str(e)}")
            raise


    def _generate_map_content(self, hierarchy: dict) -> str:
        """Generate map content from folder hierarchy with improved tree formatting."""
        def _format_folder(folder_data: dict, level: int = 0, path_prefix: str = "") -> str:
            indent = "  " * level
            content = []
            
            # Get folder path
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
            
            # Add folder purpose with emoji
            purpose = folder_data.get('purpose', 'Store and organize project files')
            content.append(f"{indent}**Purpose:** 📁 {purpose}\n")
            
            # Add files section if there are files
            if folder_data.get('files'):
                content.append(f"{indent}### Files")
                for i, file in enumerate(folder_data['files']):
                    # Use tree branches for files
                    file_branch = "├─ " if i < len(folder_data['files']) - 1 else "└─ "
                    
                    # Format role and description
                    role = file.get('role', 'DOCS 📚')  # Default role
                    description = file.get('description', '')
                    
                    # Add USE/NOT USE if not present
                    if description and ' | USE: ' not in description:
                        file_type = role.split()[0].lower()
                        if file_type == 'primary':
                            use_case = "For latest data analysis; NOT for historical records"
                        elif file_type == 'spec':
                            use_case = "For requirement definition; NOT for implementation details"
                        elif file_type == 'docs':
                            use_case = "For documentation reference; NOT for active development"
                        elif file_type == 'work':
                            use_case = "For active development; NOT for final documentation"
                        else:
                            use_case = f"For {file_type} purposes; NOT for other uses"
                        description = f"{description} | USE: {use_case}"
                    
                    # Format file entry
                    content.append(f"{indent}- **{file_branch}{file['name']}** ({role})")
                    if description:
                        content.append(f"{indent}  _{description}_\n")
                    else:
                        content.append(f"{indent}  _Stores and manages {file['name']} content_\n")
    
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
        # Set current folder for tree building
        self.fs_utils.set_current_folder(os.path.abspath(folder_path))
        
        # Build tree structure using FSUtils
        tree = self.fs_utils.build_tree_structure(
            current_path=".",
            files=files,
            subfolders=subfolders,
            max_depth=3  # Show 3 levels for non-current branches
        )
        
        # Join tree lines
        tree_str = "\n".join(tree)

        return f"""# Objective
Analyze this folder and its files:

# Current Structure
{tree_str}

# Mission Context
````
{mission_content}
````

# Instructions
Provide analysis in this format:

Folder: 📁 [Action verb + direct object, max 10 words]

Files:
- **[tree prefix] [filename]** ([CATEGORY] [EMOJI])
  _[Action verb] [technical description]_

Categories (select ONE per file):
Core: PRIMARY 📊, SPEC 📋, IMPL ⚙️, DOCS 📚
Support: CONFIG ⚡, UTIL 🛠️, TEST 🧪, BUILD 📦
Working: WORK ✍️, DRAFT 📝, TEMPLATE 📄, ARCHIVE 📂
Data: SOURCE 💾, GEN ⚡, CACHE 💫, BACKUP 💿

Rules:
- Start all descriptions with action verb
- Use technical, specific language
- Maximum 10 words per line
- Include appropriate emojis

Example correct response:
Folder: 📁 Manage authentication system configuration and credentials

Files:
- **├─ auth_config.json** (CONFIG ⚡)
  _Stores API keys and OAuth2 client credentials_
- **├─ auth_utils.py** (UTIL 🛠️)
  _Implements JWT token validation and session management_
- **└─ auth_test.py** (TEST 🧪)
  _Validates authentication flow with mock credentials_"""
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
        # Ensure we're using relative path
        if os.path.isabs(folder_path):
            folder_path = os.path.relpath(folder_path, self.project_root)
            
        # Split path into components
        path_parts = folder_path.split(os.sep)
        
        # Build tree structure showing full path hierarchy
        tree = []
        
        # Add path hierarchy
        for i, part in enumerate(path_parts):
            indent = "   " * i
            if i < len(path_parts) - 1:
                tree.append(f"{indent}├─ {part}")
            else:
                # Last part (current folder) gets the folder emoji
                tree.append(f"{indent}📂 {part}")
        
        # Add files with proper indentation
        base_indent = "   " * len(path_parts)
        for i, f in enumerate(files):
            prefix = "├─ " if i < len(files) - 1 else "└─ "
            tree.append(f"{base_indent}{prefix}{f}")
        
        tree_str = "\n".join(tree)

        return f"""#Objective
Analyze all files in this folder structure:

# Project Structure
{tree_str}

# Current Folder
{folder_path}

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
* ARCHIVE (🗄️) - Historical records

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
