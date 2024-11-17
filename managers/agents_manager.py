import os
from utils.logger import Logger

class AgentsManager:
    """Manager class for handling agents and their operations."""
    
    def __init__(self):
        self.mission_path = None
        self.logger = Logger()
        
    def generate_agents(self, mission_filepath):
        """
        Generate mission-specific agent prompts.
        
        Args:
            mission_filepath (str): Path to the mission specification file
            
        Raises:
            ValueError: If mission file is invalid or missing
            IOError: If there are file operation issues
        """
        try:
            self.mission_path = mission_filepath
            self.logger.info(f"Starting agent generation for mission: {mission_filepath}")
            
            if not self._validate_mission_file():
                raise ValueError(f"Invalid or missing mission file: {mission_filepath}")
                
            for i in range(8):
                agent_name = f"agent_{i+1}"
                try:
                    self._generate_single_agent(agent_name)
                    self.logger.info(f"Successfully generated agent: {agent_name}")
                except Exception as e:
                    self.logger.error(f"Failed to generate agent {agent_name}: {str(e)}")
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
            agent_name (str): Name of the agent
            mission_content (str): Content of the mission file
        """
        return f"""Based on the following mission specification, create a specialized agent configuration for {agent_name}.
        
Mission:
{mission_content}

Generate a markdown configuration file that defines:
1. Agent's specific role and responsibilities
2. Key capabilities and limitations
3. Interaction patterns with other agents
4. Success criteria and metrics
"""

    def _call_gpt(self, prompt):
        """
        Make a call to GPT-4o-mini to generate agent configuration.
        
        Args:
            prompt (str): The prepared prompt for GPT
        """
        # TODO: Implement actual GPT API call
        # For now, return a placeholder configuration
        return f"""# Agent Configuration
        
## Role
- Temporary placeholder configuration
- To be replaced with actual GPT-generated content

## Capabilities
- Basic file operations
- Team coordination
- Task execution

## Success Metrics
- Task completion rate
- Code quality
- Documentation coverage
"""
