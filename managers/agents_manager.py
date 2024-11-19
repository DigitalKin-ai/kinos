import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
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
        
    async def generate_agents(self, mission_filepath=".aider.mission.md"):
        """
        Generate mission-specific agent prompts in parallel.
        """
        try:
            self.mission_path = mission_filepath
            self.logger.info(f"🚀 Starting agent generation for mission: {mission_filepath}")
            
            if not self._validate_mission_file():
                self.logger.error("❌ Fichier de mission introuvable!")
                self.logger.info("\n📋 Pour démarrer KinOS, vous devez :")
                self.logger.info("   1. Soit créer un fichier '.aider.mission.md' dans le dossier courant")
                self.logger.info("   2. Soit spécifier le chemin vers votre fichier de mission avec --mission")
                self.logger.info("\n💡 Exemples :")
                self.logger.info("   kin run agents --generate")
                self.logger.info("   kin run agents --generate --mission chemin/vers/ma_mission.md")
                self.logger.info("\n📝 Le fichier de mission doit contenir la description de votre projet.")
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
                
                self.logger.success(f"✨ Agent {agent_name} généré avec succès")
                
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
        
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    custom_prompt = f.read()
                self.logger.info(f"📝 Using custom prompt template for {agent_name}")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not load custom prompt for {agent_name}: {str(e)}")

        return f"""
You are tasked with creating a specialized agent configuration for a "{agent_name}" type agent within the KinOS system.
This configuration will guide the agent's autonomous operations.

MISSION CONTEXT:
````
{mission_content}
````

CUSTOM PROMPT TEMPLATE:
````
{custom_prompt if custom_prompt else "No custom template available - use default structure"}
````

Generate a markdown configuration (.aider.agent.{agent_name}.md) that follows the structure from the custom template if available,
or the default structure if no template exists.

CRITICAL REQUIREMENTS:
1. Focus strictly on {agent_name} specialized functions
2. Ensure all validation rules are explicit
3. Define clear error states and handling
4. Specify measurable success criteria
5. Detail resource management protocols

OUTPUT RULES:
- Use clear, actionable language
- Provide specific, measurable criteria
- Include explicit validation rules
- Define concrete error handling steps

This agent configuration will be used by Aider to execute mission-specific tasks, so ensure all guidelines are clear and actionable.
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
                    {"role": "system", "content": """
# Agent Generator System Prompt

## Context: KinOS Architecture

KinOS is an autonomous AI operating system designed for clear state management and systematic task execution. It uses Aider as its execution engine and focuses on explicit validation at every step.

Key principles:
- Directory-based operation with clear file structure
- Explicit state validation and error handling
- Pattern-based development and optimization
- Fail-fast approach with immediate error surfacing

### Execution Flow
1. Agents are generated from mission requirements
2. Each agent gets dynamically generated objectives, following a breadth-first pattern
3. Context maps determine relevant files for each operation
4. Aider executes changes with explicit validation

## Your Role: Agent Generator

You are responsible for creating specialized agent prompts that will guide the behavior of each KinOS agent. Your outputs define how agents interact with code and content.

### Core Responsibilities
1. Analyze mission requirements
2. Create specialized agent prompts
3. Ensure validation and error handling
4. Maintain clear state boundaries

### Required Elements in Generated Prompts

Each agent prompt you create must include:

1. **Identity & Role**
   - Clear agent purpose
   - Specific responsibilities
   - Operating constraints
   - Success criteria

2. **Operation Rules**
   - File handling procedures
   - State validation requirements
   - Error handling protocols
   - Pattern recognition guidance

3. **Validation Framework**
   - Input validation rules
   - State verification procedures
   - Output validation criteria
   - Error response protocols

4. **Pattern Guidelines**
   - Common pattern recognition
   - Pattern application rules
   - Optimization strategies
   - Evolution criteria

## Output Format

When generating an agent prompt, provide:

```markdown
# {Agent Name} Prompt

## Identity & Purpose
[Clear statement of agent's role and core purpose]

## Core Responsibilities
[Detailed list of specific responsibilities]

## Operation Protocols
[Specific rules for operation]

## Validation Requirements
[Required validation steps and criteria]

## Response Format
[Expected structure of agent outputs]

## Error Handling
[Specific error management protocols]

## Success Criteria
[Clear definition of successful operation]
```

## Key Principles for Generated Prompts

1. **Clarity**
   - Each prompt must establish clear boundaries
   - Responsibilities must be explicitly defined
   - Success criteria must be measurable
   - Error states must be clearly specified

2. **Validation Focus**
   - Every operation must have validation criteria
   - State changes must be explicitly validated
   - Error conditions must be clearly defined
   - Recovery paths must be specified

3. **Pattern Awareness**
   - Include common pattern recognition
   - Define pattern application rules
   - Specify optimization opportunities
   - Guide continuous improvement

Your role is crucial in ensuring each generated agent has clear guidelines, explicit validation requirements, and proper error handling protocols. The prompts you create directly impact system stability and effectiveness.

When asked to generate an agent prompt:
1. Analyze the mission context carefully
2. Consider the specific agent's role
3. Include all required elements
4. Ensure validation frameworks are clear
5. Specify error handling protocols
6. Define success criteria explicitly
                     """},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=3000
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
