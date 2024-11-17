import os
from utils.logger import Logger
import openai
from dotenv import load_dotenv

class AgentsManager:
    """Manager class for handling agents and their operations."""
    
    def __init__(self):
        self.mission_path = None
        self.logger = Logger()
        load_dotenv()  # Load environment variables
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
    def generate_agents(self, mission_filepath=".aider.mission.md"):
        """
        Generate mission-specific agent prompts.
        
        Args:
            mission_filepath (str): Path to the mission specification file, defaults to .aider.mission.md
            
        Raises:
            ValueError: If mission file is invalid or missing
            IOError: If there are file operation issues
        """
        try:
            self.mission_path = mission_filepath
            self.logger.info(f"Starting agent generation for mission: {mission_filepath}")
            
            if not self._validate_mission_file():
                raise ValueError(f"Invalid or missing mission file: {mission_filepath}")
                
            # List of specific agent types
            agent_types = [
                "specification",
                "management", 
                "redaction",
                "evaluation",
                "duplication",
                "chroniqueur",
                "redondance",
                "production"
            ]
            
            for agent_type in agent_types:
                try:
                    self._generate_single_agent(agent_type)
                    self.logger.info(f"Successfully generated agent: {agent_type}")
                except Exception as e:
                    self.logger.error(f"Failed to generate agent {agent_type}: {str(e)}")
                    raise
                    
        except Exception as e:
            self.logger.error(f"Agent generation failed: {str(e)}")
            raise
            
    def _validate_mission_file(self):
        """
        Validate that mission file exists and is readable.
        
        Returns:
            bool: True if file is valid, False otherwise
        """
        try:
            return os.path.exists(self.mission_path) and os.access(self.mission_path, os.R_OK)
        except Exception as e:
            self.logger.error(f"Error validating mission file: {str(e)}")
            return False
        
    def _generate_single_agent(self, agent_name):
        """
        Generate a single agent configuration file.
        
        Args:
            agent_name (str): Name for the agent
            
        Raises:
            IOError: If there are issues with file operations
            Exception: For other unexpected errors
        """
        try:
            # 1. Load mission content
            with open(self.mission_path, 'r') as f:
                mission_content = f.read()
            
            # 2. Prepare agent prompt
            prompt = self._create_agent_prompt(agent_name, mission_content)
            self.logger.debug(f"Created prompt for agent: {agent_name}")
            
            # 3. Make GPT call and get response
            agent_config = self._call_gpt(prompt)
            self.logger.debug(f"Received GPT response for agent: {agent_name}")
            
            # 4. Save agent configuration
            output_path = f".aider.agent.{agent_name}.md"
            with open(output_path, 'w') as f:
                f.write(agent_config)
                
        except IOError as e:
            self.logger.error(f"File operation error for agent {agent_name}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error generating agent {agent_name}: {str(e)}")
            raise

    def _create_agent_prompt(self, agent_name, mission_content):
        """
        Create the prompt for GPT to generate an agent configuration.
        
        Args:
            agent_name (str): Name/type of the agent
            mission_content (str): Content of the mission file
        """
        return f"""Based on the following mission specification, create a specialized agent configuration for an agent of type "{agent_name}".

Mission:
{mission_content}

Generate a markdown configuration file that defines:
1. Agent's specific role and responsibilities as a {agent_name} type agent
2. Key capabilities and limitations specific to {agent_name} functions
3. Interaction patterns with other agents
4. Success criteria and metrics for {agent_name} operations

The configuration must focus specifically on {agent_name} type operations and responsibilities.
"""

    def _call_gpt(self, prompt):
        """
        Make a call to GPT to generate agent configuration.
        
        Args:
            prompt (str): The prepared prompt for GPT
            
        Returns:
            str: Generated agent configuration
            
        Raises:
            Exception: If API call fails
        """
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using the correct Omni model
                messages=[
                    {"role": "system", "content": "You are a specialized AI agent configuration generator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract the generated configuration from the response
            config = response.choices[0].message.content
            
            # Validate basic structure
            if not all(marker in config for marker in ["# Agent Configuration", "## Role", "## Capabilities"]):
                self.logger.warning("Generated configuration missing required sections")
                # Fall back to template if response is malformed
                return self._get_fallback_config()
                
            return config
            
        except Exception as e:
            self.logger.error(f"GPT API call failed: {str(e)}")
            # Fall back to template in case of API failure
            return self._get_fallback_config()

    def _get_fallback_config(self):
        """Return a fallback configuration if API call fails."""
        return """# Agent Configuration
        
## Role
- Temporary fallback configuration
- Generated due to API call failure

## Capabilities
- Basic file operations
- Team coordination
- Task execution

## Success Metrics
- Task completion rate
- Code quality
- Documentation coverage
"""
