import os
import asyncio
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
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

    def _get_available_files(self):
        """Get list of available files respecting ignore patterns."""
        ignore_patterns = self._get_ignore_patterns()
        available_files = []
        
        for root, dirs, files in os.walk('.'):
            # Remove ignored directories to prevent walking into them
            dirs[:] = [d for d in dirs if not any(
                fnmatch.fnmatch(os.path.join(root, d), pattern) 
                for pattern in ignore_patterns
            )]
            
            for file in files:
                file_path = os.path.join(root, file)
                # Convert to relative path with forward slashes
                rel_path = os.path.relpath(file_path, '.').replace(os.sep, '/')
                
                # Skip files matching ignore patterns
                if not any(fnmatch.fnmatch(rel_path, pattern) for pattern in ignore_patterns):
                    available_files.append(rel_path)
                    
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
                
            # Get available files
            available_files = self._get_available_files()
            self.logger.debug(f"📁 Available files: {available_files}")
            
            # Load required content
            mission_content = self._read_file(mission_filepath)
            objective_content = self._read_file(objective_filepath)
            agent_content = self._read_file(agent_filepath)
            
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
        """Read content from file."""
        try:
            with open(filepath, 'r') as f:
                return f.read()
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
                agent_content,
                available_files
            )
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """
You are a context mapping system that selects relevant files for an agent's next operation.
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

    def _create_map_prompt(self, mission_content, objective_content, agent_content, available_files):
        """Create prompt for context map generation."""
        # Load global map content if it exists
        global_map_content = ""
        if os.path.exists("map.md"):
            try:
                with open("map.md", 'r', encoding='utf-8') as f:
                    global_map_content = f.read()
            except Exception as e:
                self.logger.warning(f"⚠️ Could not read global map: {str(e)}")
                # Continue without global map content
        
        return f"""Based on the following context, select the relevant files needed for the next operation.

Mission:
{mission_content}

Current Objective:
{objective_content}

Agent Configuration:
{agent_content}

Global Project Map:
{global_map_content}

Available Files:
{chr(10).join(f"- {f}" for f in available_files)}

Using the global map information about file contents, select only the most relevant files needed to complete the current objective.
Consider:
- File contents and purposes described in the global map
- Current state and implementation status of each file
- Dependencies between files
- Relevance to the current objective

Return a list of only the files needed to complete the current objective (aim for 8-10).
Format as a simple markdown list under a "# Context Map" heading.
"""


    def _save_map(self, filepath, content):
        """Save context map content to file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            self.logger.error(f"Error saving map to {filepath}: {str(e)}")
            raise

    async def initialize_global_map(self):
        """
        Initialize or reset the global map file with summaries of all project files.
        Processes files in batches of 10 for better performance.
        """
        try:
            self.logger.info("🗺️ Initializing global project map...")
            
            # Initialize tokenizer for GPT-4
            tokenizer = tiktoken.encoding_for_model("gpt-4")
            
            # Get all available files
            available_files = self._get_available_files()
            total_files = len(available_files)
            
            # Create map header
            map_content = "# Project Map\n\n"
            
            # Process files in batches of 10
            batch_size = 10
            for i in range(0, total_files, batch_size):
                batch = available_files[i:i+batch_size]
                batch_tasks = []
                
                self.logger.info(f"📊 Processing batch {i//batch_size + 1}/{(total_files+batch_size-1)//batch_size} ({len(batch)} files)")
                
                # Create tasks for batch
                for filepath in batch:
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        token_count = len(tokenizer.encode(file_content))
                        
                        # Create task for file summary generation
                        task = asyncio.create_task(self._generate_file_summary_async(filepath, file_content))
                        batch_tasks.append((filepath, token_count, task))
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not read {filepath}: {str(e)}")
                        continue
                
                # Wait for all summaries in batch
                for filepath, token_count, task in batch_tasks:
                    try:
                        summary = await task
                        map_content += f"{filepath} ({token_count} tokens) {summary}\n"
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not process {filepath}: {str(e)}")
                        continue
                
                # Small delay between batches to avoid rate limits
                await asyncio.sleep(1)
                    
            # Save map file
            with open("map.md", 'w', encoding='utf-8') as f:
                f.write(map_content)
                
            self.logger.success("✨ Global project map initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize global map: {str(e)}")
            raise

    def update_global_map(self, modified_file_path):
        """Update global map with latest file summary after a commit."""
        try:
            # Read current global map content
            global_map_content = ""
            if os.path.exists("map.md"):
                with open("map.md", 'r', encoding='utf-8') as f:
                    global_map_content = f.read()

            # Read modified file content
            with open(modified_file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            # Get token count
            tokenizer = tiktoken.encoding_for_model("gpt-4")
            token_count = len(tokenizer.encode(file_content))

            # Generate new summary with global context
            client = openai.OpenAI()
            prompt = f"""
Analyze this file in the context of the entire project and explain its unique role.

Current Global Project Map:
{global_map_content}

Modified File: {modified_file_path}
Content:
{file_content}

Provide a one-line summary (max 300 chars) that:
1. Explains what makes this file DIFFERENT from other files, Highlights its SPECIFIC purpose
2. Describe the file, not the content of the file
3. Avoids repeating information already present in other files
4. Uses emojis to indicate the file's primary function
5. Indicates the current advancement of the file

Use bold text (**) for key concepts.
"""

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

            # Update map.md with new summary
            self._update_map_file(modified_file_path, token_count, summary)

            self.logger.debug(f"🔄 Updated global map for: {modified_file_path}")

        except Exception as e:
            self.logger.error(f"Failed to update global map: {str(e)}")
            raise

    async def _generate_file_summary_async(self, filepath, content):
        """Async version of file summary generation."""
        try:
            client = openai.OpenAI()
            prompt = f"""
Analyze this file and provide a concise summary of its current state and content.
Focus on:
- Main purpose and functionality
- Key components/sections
- Implementation status
- Notable patterns or issues

File: {filepath}
Content:
{content}

Provide a one-line summary (max 250 chars) that captures the essence and current state. Use some bold and emojis to increase readability.
"""
            
            response = await asyncio.to_thread(
                lambda: client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a code analysis system that provides concise, informative file summaries."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=100
                )
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to generate file summary: {str(e)}")
            raise

    def _update_map_file(self, filepath, summary):
        """Update map.md with new file summary."""
        try:
            map_path = "map.md"
            updated_lines = []
            
            # Get token count for the file
            tokenizer = tiktoken.encoding_for_model("gpt-4")
            with open(filepath, 'r', encoding='utf-8') as f:
                file_content = f.read()
            token_count = len(tokenizer.encode(file_content))
            
            file_entry = f"{filepath} ({token_count} tokens) {summary}"
            entry_updated = False
            
            # Read existing map if it exists
            if os.path.exists(map_path):
                with open(map_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # Update existing entry or keep line
                for line in lines:
                    if line.startswith(filepath):
                        updated_lines.append(file_entry + '\n')
                        entry_updated = True
                    else:
                        updated_lines.append(line)
                        
            # Add new entry if not updated
            if not entry_updated:
                updated_lines.append(file_entry + '\n')
                
            # Write updated map
            with open(map_path, 'w', encoding='utf-8') as f:
                if not updated_lines:  # New file
                    f.write("# Project Map\n\n")
                f.writelines(updated_lines)
                
        except Exception as e:
            self.logger.error(f"Failed to update map file: {str(e)}")
            raise
