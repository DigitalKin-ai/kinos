import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from utils.logger import Logger
import openai
from dotenv import load_dotenv

class AgentsManager:
    """Manager class for handling agents and their operations."""
    
    def __init__(self, model="gpt-4o-mini"):
        self.mission_path = None
        self.logger = Logger()
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
                "redaction",
                "evaluation",
                "deduplication",
                "chroniqueur",
                "redondance",
                "production",
                "chercheur",
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
            return os.path.exists(self.mission_path) and os.access(self.mission_path, os.R_OK)
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
        with open(self.mission_path, 'r') as f:
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
        # Try to load custom prompt template
        prompt_path = f"prompts/{agent_name}.md"
        custom_prompt = ""

        # Load global map content if it exists
        global_map_content = ""
        if os.path.exists("map.md"):
            try:
                with open("map.md", 'r', encoding='utf-8') as f:
                    global_map_content = f.read()
            except Exception as e:
                self.logger.warning(f"⚠️ Could not read global map: {str(e)}")
                # Continue without global map content
        
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    custom_prompt = f.read()
                self.logger.info(f"📝 Using custom prompt template for {agent_name}")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not load custom prompt for {agent_name}: {str(e)}")

        # Ensure we're getting the complete mission content
        self.logger.debug(f"Mission content length: {len(mission_content)} characters")
        
        return f"""
# Generate KinOS Agent Configuration

Using the provided analysis framework, generate an Aider agent configuration for the {agent_name} role. Your output will be saved as .aider.agent.{agent_name}.md and will guide Aider's file operations.

## Input Context

MISSION (COMPLETE):
````
{mission_content}
````

CURRENT PROJECT MAP:
````
{global_map_content}
````

ANALYSIS FRAMEWORK:
````
{custom_prompt if custom_prompt else "Using default KinOS analysis framework"}
````

## Generation Process

1. Analyze Framework Questions
   - Work through each section of the analysis framework
   - Consider how each question applies to this specific agent type for this mission
   - Identify the most relevant patterns and triggers
   - Determine concrete file operations needed

2. Translate Analysis to Operations
   - Transform insights into specific file monitoring rules
   - Define clear Aider operation patterns
   - Establish explicit content validation criteria
   - Specify optimization and deduplication strategies

3. Structure Agent Configuration
   - Create clear file monitoring directives
   - Define specific Aider operation triggers
   - Establish concrete validation rules
   - Document success indicators

Your output should be a practical, actionable configuration focused on concrete file operations via Aider. Ensure all directives are grounded in KinOS's file-based architecture.
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
                model="gpt-4o",  # Using the BIG Omni model!
                messages=[
                    {"role": "system", "content": """
# KinOS Agent Generator System Prompt

You are the generator component of KinOS, creating specialized prompts for Aider-based autonomous agents. Your understanding of KinOS's core architecture is essential for generating relevant and executable prompts.

## KinOS Operational Context

### Core Architecture
- File-based state management (no direct inter-agent communication)
- Aider as execution engine for all file modifications
- Atomic file operations with explicit validation
- Directory-based mission contextualization

### Agent Operation Model
- Each agent independently monitors specific files
- Changes are made only through Aider-mediated file operations
- All state exists in files - no external state management
- Validation occurs through file content verification

### File Interaction Patterns
- Read: Monitor designated files for changes
- Analyze: Process file content against validation rules
- Modify: Request changes through Aider
- Validate: Verify file state post-modification

## Prompt Generation Principles

1. **File-Centric Operation**
   - Every instruction must relate to file operations
   - State changes only through file modifications
   - All validation based on file content
   - Clear file scope definition

2. **Aider-Specific Direction**
   - Instructions compatible with Aider's capabilities
   - Clear file modification protocols
   - Explicit success validation criteria
   - Error detection through file state

3. **Mission Contextualization**
   - Derive requirements from mission files
   - Map file dependencies and interactions
   - Define file-based validation rules
   - Establish clear file modification boundaries

4. **Pattern Integration**
   - File monitoring patterns
   - Content validation patterns
   - Error detection patterns
   - Recovery operation patterns

## Validation Requirements

Every generated prompt must ensure:
- All operations reference specific files
- State validation through file content
- Error detection via file state
- Recovery through file operations
- Clear file scope boundaries

Your prompts must enable agents to operate autonomously within KinOS's file-based architecture, ensuring all actions and validations occur through proper file operations mediated by Aider.
                     """},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=4000
            )
            
            # Extract the generated configuration from the response
            config = response.choices[0].message.content
            
            # Log full response for debugging
            self.logger.debug(f"OpenAI Response: {response}")
            
            return config
            
        except Exception as e:
            self.logger.error(f"GPT API call failed. Error: {str(e)}")
            self.logger.error(f"Last response received: {response if 'response' in locals() else 'No response'}")
            raise
