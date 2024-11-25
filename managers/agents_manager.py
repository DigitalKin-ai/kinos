import os
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
from utils.logger import Logger
import openai
from dotenv import load_dotenv

class AgentsManager:
    """Manager class for handling agents and their operations."""
    
    def __init__(self, model=None):
        self.mission_path = None
        self.logger = Logger(model=model)
        self.model = model
        load_dotenv()  # Load environment variables
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
    async def generate_agents(self, mission_filepath=".aider.mission.md"):
        """
        Generate mission-specific agent prompts in parallel.
        """
        try:
            self.mission_path = mission_filepath
            self.logger.info(f"🚀 Starting agent generation for mission: {mission_filepath}")
            
            if not self._validate_mission_file():
                self.logger.error("❌ Mission file not found!")
                self.logger.info("\n📋 To start KinOS, you must:")
                self.logger.info("   1. Either create a '.aider.mission.md' file in the current folder")
                self.logger.info("   2. Or specify the path to your mission file with --mission")
                self.logger.info("\n💡 Examples:")
                self.logger.info("   kin run agents --generate")
                self.logger.info("   kin run agents --generate --mission path/to/my_mission.md")
                self.logger.info("\n📝 The mission file must contain your project description.")
                raise SystemExit(1)
                
            # List of specific agent types
            agent_types = [
                "specification",
                "management", 
                "writing",
                "evaluation",
                "deduplication",
                "chronicler",
                "redundancy",
                "production",
                "researcher",
                "integration"
            ]
            
            # Create tasks for parallel execution
            tasks = []
            for agent_type in agent_types:
                tasks.append(self._generate_single_agent_async(agent_type))
                
            # Execute all tasks in parallel and wait for completion
            await asyncio.gather(*tasks)
            
        except Exception as e:
            self.logger.error(f"❌ Agent generation failed: {str(e)}")
            raise
            
    def _validate_mission_file(self):
        """
        Validate that mission file exists and is readable.
        
        Returns:
            bool: True if file is valid, False otherwise
        """
        try:
            if not (os.path.exists(self.mission_path) and os.access(self.mission_path, os.R_OK)):
                return False
                
            # Try reading with UTF-8 to validate encoding
            try:
                with open(self.mission_path, 'r', encoding='utf-8') as f:
                    f.read()
                return True
            except UnicodeDecodeError:
                self.logger.error(f"❌ Mission file must be in UTF-8 encoding: {self.mission_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"⚠️ Error validating mission file: {str(e)}")
            return False
        
    async def _generate_single_agent_async(self, agent_name):
        """
        Asynchronous version of _generate_single_agent.
        """
        try:
            # Use ThreadPoolExecutor for CPU-bound operations
            with ThreadPoolExecutor() as pool:
                # Load mission content
                mission_content = await asyncio.get_event_loop().run_in_executor(
                    pool,
                    self._read_mission_content
                )
                
                # Create agent prompt
                prompt = self._create_agent_prompt(agent_name, mission_content)
                self.logger.debug(f"📝 Created prompt for agent: {agent_name}")
                
                # Make GPT call and get response
                agent_config = await asyncio.get_event_loop().run_in_executor(
                    pool,
                    lambda: self._call_gpt(prompt)
                )
                self.logger.debug(f"🤖 Received GPT response for agent: {agent_name}")
                
                # Save agent configuration
                output_path = f".aider.agent.{agent_name}.md"
                await asyncio.get_event_loop().run_in_executor(
                    pool,
                    lambda: self._save_agent_config(output_path, agent_config)
                )
                
                self.logger.success(f"✨ Agent {agent_name} successfully generated")
                
        except Exception as e:
            self.logger.error(f"Failed to generate agent {agent_name}: {str(e)}")
            raise

    def _read_mission_content(self):
        """Helper method to read mission content."""
        with open(self.mission_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _save_agent_config(self, output_path, content):
        """Helper method to save agent configuration."""
        with open(output_path, 'w') as f:
            f.write(content)

    def _create_agent_prompt(self, agent_name, mission_content):
        """
        Create the prompt for GPT to generate a specialized agent configuration.
        
        Args:
            agent_name (str): Name/type of the agent to generate
            mission_content (str): Content of the mission specification file
        
        Returns:
            str: Detailed prompt for agent generation
        """
        # Get the KinOS installation directory
        if getattr(sys, 'frozen', False):
            # If running as compiled executable
            install_dir = os.path.dirname(sys.executable)
        else:
            # If running from source
            install_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        # Look for prompts in the installation directory
        prompt_path = os.path.join(install_dir, "prompts", f"{agent_name}.md")
        self.logger.debug(f"Looking for prompt at: {prompt_path}")
        
        custom_prompt = ""
    
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    custom_prompt = f.read()
                if not custom_prompt.strip():
                    raise ValueError(f"Prompt file {prompt_path} exists but is empty")
                self.logger.info(f"📝 Using custom prompt template for {agent_name}")
            except Exception as e:
                self.logger.error(f"❌ Failed to load prompt for {agent_name}: {str(e)}")
                raise ValueError(f"Could not load required prompt file {prompt_path}: {str(e)}")

        # Ensure we're getting the complete mission content
        self.logger.debug(f"Mission content length: {len(mission_content)} characters")
        
        return f"""
# Generate KinOS Agent Configuration

Generate a role definition and plan for the {agent_name} agent that fulfills the mission while following the analysis framework.

## Context Analysis
1. Mission Details
````
{mission_content}
````

2. Analysis Framework
````
{custom_prompt}
````

## Requirements

1. Mission Alignment
   - How agent's role serves mission objectives
   - Critical mission needs to address
   - Mission-specific success criteria

2. Framework Application
   - Apply framework questions to mission context
   - Use framework to structure mission approach
   - Define mission-specific validation points

3. Role Definition
   - Core responsibilities for mission completion
   - Interaction patterns within mission scope
   - Mission-aligned success criteria

4. High-Level Plan
   - Major mission milestones
   - Systematic approach to mission goals
   - Quality standards for mission deliverables

Your output should clearly show how this agent will contribute to mission success through the lens of the analysis framework.

Example Sections:
- Mission Understanding
- Role in Mission Completion
- Framework-Guided Approach
- Key Objectives & Milestones
- Quality Standards
- Success Criteria
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
            self.logger.debug("\n🤖 AGENT CONFIGURATION PROMPT:")
            self.logger.debug("=== System Message ===")
            self.logger.debug("""
# KinOS Agent Generator

You create strategic role definitions for KinOS agents by applying specialized analysis frameworks.

## Operational Context
- Agent operates through Aider file operations
- Main loop handles all triggers and timing
- Single-step file modifications only
- Directory-based mission scope

## Framework Integration
1. Question Analysis
   - Process each framework section
   - Extract relevant guidelines
   - Apply to current context

2. Role Mapping
   - Map responsibilities to framework sections
   - Align capabilities with framework requirements
   - Define boundaries using framework structure

3. Planning Through Framework
   - Use framework sections as planning guides
   - Ensure comprehensive coverage
   - Maintain framework-aligned validation

## Core Requirements
1. Mission Contribution
   - Framework-guided responsibilities
   - Framework-aligned success metrics
   - Quality standards from framework

2. Team Integration
   - Framework-based coordination
   - Shared objective alignment
   - Quality interdependencies

Remember: 
- Answer framework questions practically
- Keep focus on achievable file operations
- Use framework to structure planning
- Maintain mission alignment
""")
            self.logger.debug("\n=== User Message ===")
            self.logger.debug(prompt)

            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": """
# KinOS Agent Generator

You create strategic role definitions for KinOS agents by applying specialized analysis frameworks.

## Operational Context
- Agent operates through Aider file operations
- Main loop handles all triggers and timing
- Single-step file modifications only
- Directory-based mission scope

## Framework Integration
1. Question Analysis
   - Process each framework section
   - Extract relevant guidelines
   - Apply to current context

2. Role Mapping
   - Map responsibilities to framework sections
   - Align capabilities with framework requirements
   - Define boundaries using framework structure

3. Planning Through Framework
   - Use framework sections as planning guides
   - Ensure comprehensive coverage
   - Maintain framework-aligned validation

## Core Requirements
1. Mission Contribution
   - Framework-guided responsibilities
   - Framework-aligned success metrics
   - Quality standards from framework

2. Team Integration
   - Framework-based coordination
   - Shared objective alignment
   - Quality interdependencies

Remember: 
- Answer framework questions practically
- Keep focus on achievable file operations
- Use framework to structure planning
- Maintain mission alignment
"""},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=4000
            )
            
            # Extract the generated configuration from the response
            config = response.choices[0].message.content
            
            # Log the response content
            self.logger.debug("\n✨ AGENT CONFIGURATION RESPONSE:")
            self.logger.debug(config)
            
            return config
            
        except Exception as e:
            self.logger.error(f"GPT API call failed. Error: {str(e)}")
            if 'response' in locals():
                self.logger.error("\n🔍 Last Response Details:")
                self.logger.error(f"Status: {response.status}")
                self.logger.error(f"Headers: {response.headers}")
                self.logger.error(f"Content: {response.choices[0].message.content if response.choices else 'No content'}")
            raise
