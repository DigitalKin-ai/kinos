import os
import asyncio
import logging
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
    def _analyze_file(self, filename: str, folder_context: dict) -> dict:
        """Analyze single file's role and purpose."""
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

    def _create_file_analysis_prompt(self, filename: str, folder_context: dict) -> str:
        """Create prompt for analyzing a single file's role."""
        return f"""Analyze this file's role in its folder:

Filename: {filename}
Folder Purpose: {folder_context['purpose']}

Determine the file's:
1. Technical role (using emoji categories below)
2. Specific purpose in this folder
3. How it supports folder's purpose

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

    def _analyze_folder_hierarchy(self, folder_path: str, mission_content: str, objective_content: str) -> dict:
        """
        Analyze folder and all its subfolders recursively, maintaining hierarchy.
        
        Returns:
            dict: Hierarchical structure like:
            {
                'path': folder_path,
                'purpose': 'Folder purpose description',
                'files': [
                    {
                        'name': 'file.py',
                        'role': '⚙️ IMPL',
                        'description': 'File purpose...'
                    }
                ],
                'subfolders': {
                    'subfolder_name': {
                        'path': subfolder_path,
                        'purpose': 'Subfolder purpose...',
                        'files': [...],
                        'subfolders': {...}
                    }
                },
                'relationships': {
                    'parent': 'How this folder relates to parent',
                    'siblings': 'How it relates to sibling folders',
                    'children': 'How subfolders are organized'
                }
            }
        """
        try:
            # Get immediate files and subfolders
            files = self._get_folder_files(folder_path)
            subfolders = self._get_subfolders(folder_path)
            
            # Get folder's own context first
            folder_context = self._get_folder_context(
                folder_path,
                files,
                subfolders,
                mission_content,
                objective_content
            )
            
            # Build hierarchical structure
            hierarchy = {
                'path': folder_path,
                'purpose': folder_context['purpose'],
                'files': [self._analyze_file(f, folder_context) for f in files],
                'subfolders': {},
                'relationships': folder_context['relationships']
            }
            
            # Recursively analyze subfolders
            for subfolder in subfolders:
                subfolder_path = os.path.join(folder_path, subfolder)
                hierarchy['subfolders'][subfolder] = self._analyze_folder_hierarchy(
                    subfolder_path,
                    mission_content,
                    objective_content
                )
                
            return hierarchy
            
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

    def _get_folder_context(self, folder_path: str, files: list, subfolders: list,
                          mission_content: str, objective_content: str) -> dict:
        """Get folder purpose and relationships using GPT."""
        try:
            client = openai.OpenAI()
            prompt = self._create_folder_context_prompt(
                folder_path, files, subfolders,
                mission_content, objective_content
            )
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a technical architect analyzing project structure and organization."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse response into structure
            content = response.choices[0].message.content
            lines = content.split('\n')
            
            context = {
                'purpose': '',
                'relationships': {
                    'parent': '',
                    'siblings': '',
                    'children': ''
                }
            }
            
            current_section = None
            for line in lines:
                if line.startswith('Purpose:'):
                    current_section = 'purpose'
                    context['purpose'] = line.replace('Purpose:', '').strip()
                elif line.startswith('Parent:'):
                    current_section = 'parent'
                    context['relationships']['parent'] = line.replace('Parent:', '').strip()
                elif line.startswith('Siblings:'):
                    current_section = 'siblings'
                    context['relationships']['siblings'] = line.replace('Siblings:', '').strip()
                elif line.startswith('Children:'):
                    current_section = 'children'
                    context['relationships']['children'] = line.replace('Children:', '').strip()
                    
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get folder context for {folder_path}: {str(e)}")
            raise

    def _analyze_file(self, filename: str, folder_context: dict) -> dict:
        """Analyze single file's role and purpose."""
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
