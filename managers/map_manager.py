import os
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

    def generate_map(self, mission_filepath=".aider.mission.md", 
                    objective_filepath=None, 
                    agent_filepath=None):
        """
        Generate a context map for an agent based on mission, objective and agent configuration.
        
        Args:
            mission_filepath (str): Path to mission specification file
            objective_filepath (str): Path to current objective file
            agent_filepath (str): Path to agent configuration file
            
        Raises:
            ValueError: If required files are invalid or missing
            IOError: If there are file operation issues
        """
        try:
            self.logger.info(f"Generating map for agent: {agent_filepath}")
            
            # Validate input files
            if not all(self._validate_file(f) for f in [mission_filepath, objective_filepath, agent_filepath]):
                raise ValueError("Invalid or missing input files")
                
            # Extract agent name from filepath
            agent_name = self._extract_agent_name(agent_filepath)
            
            # Load content from files
            mission_content = self._read_file(mission_filepath)
            objective_content = self._read_file(objective_filepath)
            agent_content = self._read_file(agent_filepath)
            
            # Generate map via GPT
            context_map = self._generate_map_content(mission_content, objective_content, agent_content, agent_name)
            
            # Save map
            output_path = f".aider.map.{agent_name}.md"
            self._save_map(output_path, context_map)
            
            self.logger.info(f"Successfully generated context map for {agent_name}")
            
        except Exception as e:
            self.logger.error(f"Map generation failed: {str(e)}")
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

    def _generate_map_content(self, mission_content, objective_content, agent_content, agent_name):
        """Generate context map content using GPT."""
        try:
            client = openai.OpenAI()
            prompt = self._create_map_prompt(mission_content, objective_content, agent_content, agent_name)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """
## Context Map Generator

You are a specialized context mapping system within KinOS. Your role is to analyze the current state and determine which files and resources are relevant for the next agent operation.

Key responsibilities:
1. Identify relevant files for the current objective
2. Map dependencies between components
3. Specify access patterns (read/write)
4. Define resource boundaries

Your output must be precise and actionable, as it will directly guide file access during execution.

Format your response as a markdown document with clear sections:

# Context Map

## Primary Files
- List of main files to be modified
- Access patterns for each

## Supporting Files
- Reference files needed
- Read-only resources

## Dependencies
- Required external resources
- System dependencies

## Access Patterns
- Specific read/write patterns
- Lock requirements
- State validation needs
"""},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            context_map = response.choices[0].message.content
            
            # Validate map structure
            if not self._validate_map_content(context_map):
                raise ValueError("Generated map missing required sections")
                
            return context_map
            
        except Exception as e:
            self.logger.error(f"GPT API call failed: {str(e)}")
            raise

    def _create_map_prompt(self, mission_content, objective_content, agent_content, agent_name):
        """Create prompt for context map generation."""
        return f"""
Based on the following context, generate a detailed context map for the {agent_name} agent's next operation.

Mission Context:
{mission_content}

Current Objective:
{objective_content}

Agent Configuration:
{agent_content}

Generate a markdown-formatted context map that specifies:
1. Primary files that will be modified
2. Supporting files needed for reference
3. Required dependencies and resources
4. Specific access patterns and permissions
5. State validation requirements

The map must be:
- Specific to the current objective
- Clear about file access patterns
- Explicit about dependencies
- Focused on required resources only
"""

    def _validate_map_content(self, content):
        """Validate generated map has required sections."""
        required_sections = [
            "# Context Map",
            "## Primary Files",
            "## Supporting Files",
            "## Dependencies",
            "## Access Patterns"
        ]
        return all(section in content for section in required_sections)

    def _save_map(self, filepath, content):
        """Save context map content to file."""
        try:
            with open(filepath, 'w') as f:
                f.write(content)
        except Exception as e:
            self.logger.error(f"Error saving map to {filepath}: {str(e)}")
            raise
