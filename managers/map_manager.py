import os
from pathlib import Path
import fnmatch
from utils.logger import Logger
import openai
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
        return f"""Based on the following context, select the relevant files needed for the next operation.

Mission:
{mission_content}

Current Objective:
{objective_content}

Agent Configuration:
{agent_content}

Available Files:
{chr(10).join(f"- {f}" for f in available_files)}

Return a list of only the files needed to complete the current objective.
Format as a simple markdown list under a "# Context Map" heading.
"""


    def _save_map(self, filepath, content):
        """Save context map content to file."""
        try:
            with open(filepath, 'w') as f:
                f.write(content)
        except Exception as e:
            self.logger.error(f"Error saving map to {filepath}: {str(e)}")
            raise
