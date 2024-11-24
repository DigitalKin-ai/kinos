import os
import random
import asyncio
import time
import openai
import threading
from concurrent.futures import ThreadPoolExecutor
from utils.logger import Logger
from managers.agents_manager import AgentsManager
from managers.objective_manager import ObjectiveManager
from managers.aider_manager import AiderManager

# Configuration constants
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_AGENT_COUNT = 10
AGENT_START_DELAY = 10  # seconds between agent starts
DEFAULT_MISSION_FILE = ".aider.mission.md"

class AgentRunner:
    """Runner class for executing and managing agent operations.
    
    This class handles the parallel execution of AI agents, managing their lifecycle
    and coordinating their operations. It ensures proper resource management and
    synchronization between agents.
    
    Attributes:
        logger (Logger): Logging utility instance
        agents_manager (AgentsManager): Manager for agent generation and configuration
        objective_manager (ObjectiveManager): Manager for agent objectives
        aider_manager (AiderManager): Manager for aider operations
        _active_agents (set): Set of currently active agent names
        _agent_lock (asyncio.Lock): Lock for synchronizing agent operations
    """
    
    def __init__(self, model="gpt-4o-mini"):
        """Initialize the runner with required managers and synchronization primitives."""
        self.logger = Logger(model=model)
        self.agents_manager = AgentsManager(model=model)
        self.objective_manager = ObjectiveManager(model=model)
        self.aider_manager = AiderManager(model=model)
        self._active_agents = set()  # Track active agents
        self._agent_lock = asyncio.Lock()  # Use asyncio.Lock for async operations
        self.model = model

    def _validate_mission_file(self, mission_filepath):
        """
        Validate that mission file exists and is readable.
        
        Args:
            mission_filepath (str): Path to mission file
            
        Returns:
            bool: True if file is valid, False otherwise
            
        Side Effects:
            Logs error messages if validation fails
        """
        if not os.path.exists(mission_filepath):
            self.logger.error("❌ Mission file not found!")
            self.logger.info("\n📋 To start KinOS, you must:")
            self.logger.info("   1. Either create a '.aider.mission.md' file in the current folder")
            self.logger.info("   2. Or specify the path to your mission file with --mission")
            self.logger.info("\n💡 Examples:")
            self.logger.info("   kin run agents --generate")
            self.logger.info("   kin run agents --generate --mission path/to/my_mission.md")
            self.logger.info("\n📝 The mission file must contain your project description.")
            return False
        
        if not os.access(mission_filepath, os.R_OK):
            self.logger.error(f"❌ Cannot read mission file: {mission_filepath}")
            return False
            
        return True

    async def initialize(self):
        """Initialize async components of the runner."""
        return self

    @classmethod
    async def create(cls, model="gpt-4o-mini"):
        """Factory method to create and initialize an AgentRunner instance."""
        runner = cls(model=model)
        return await runner.initialize()
        
    async def run(self, mission_filepath=DEFAULT_MISSION_FILE, generate_agents=False, 
                 agent_count=DEFAULT_AGENT_COUNT, model=DEFAULT_MODEL):
        """Run agents in parallel."""
        try:
            # First validate mission file
            if not os.path.exists(mission_filepath):
                self.logger.error("❌ Mission file not found!")
                self.logger.info("\n📋 To start KinOS, you must:")
                self.logger.info("   1. Either create a '.aider.mission.md' file in the current folder")
                self.logger.info("   2. Or specify the path to your mission file with --mission")
                self.logger.info("\n💡 Examples:")
                self.logger.info("   kin run agents --generate")
                self.logger.info("   kin run agents --generate --mission path/to/my_mission.md")
                self.logger.info("\n📝 The mission file must contain your project description.")
                raise SystemExit(1)

            # Then check for missing agents
            missing_agents = self._agents_exist(force_regenerate=generate_agents)
            if missing_agents:
                self.logger.info("🔄 Generating agents automatically...")
                await self.agents_manager.generate_agents(mission_filepath)

            self.logger.info(f"🚀 Starting with {agent_count} agents in parallel")

            # Create initial pool of agents
            tasks = set()
            available_agents = self._get_available_agents()
            if not available_agents:
                raise ValueError("No agents available to run")
                
            # Create initial tasks up to agent_count
            for i in range(min(agent_count, len(available_agents))):
                task = asyncio.create_task(
                    self._run_single_agent_cycle(mission_filepath, model)
                )
                tasks.add(task)
                await asyncio.sleep(10)  # 10 second delay between each start

            if not tasks:
                raise ValueError("No tasks could be created")

            # Maintain active agent count
            while tasks:
                # Wait for an agent to complete
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                
                # Handle completed agents
                for task in done:
                    try:
                        await task  # Get potential errors
                    except Exception as e:
                        self.logger.error(f"Agent task failed: {str(e)}")
                    
                    # Refresh available agents list
                    available_agents = self._get_available_agents()
                    
                    # Create new agent to replace completed one
                    if len(pending) < agent_count and available_agents:
                        await asyncio.sleep(3)  # Delay before starting new agent
                        new_task = asyncio.create_task(
                            self._run_single_agent_cycle(mission_filepath, model)
                        )
                        pending.add(new_task)
                        self.logger.info(f"🔄 Replaced completed agent. Active agents: {len(pending)}/{agent_count}")
                    else:
                        self.logger.warning(f"⚠️ Could not replace agent. Pending: {len(pending)}, Target: {agent_count}, Available: {len(available_agents)}")
                
                # Update tasks set
                tasks = pending

        except Exception as e:
            self.logger.error(f"Error during execution: {str(e)}")
            raise
            
    def _get_agent_emoji(self, agent_type):
        """Get the appropriate emoji for an agent type."""
        agent_emojis = {
            'specification': '📌',
            'management': '🧭',
            'redaction': '✍️',
            'evaluation': '⚖️',
            'deduplication': '👥',
            'chroniqueur': '📜',
            'redondance': '🎭',
            'production': '🏭',
            'chercheur': '🔬',
            'integration': '🌐' 
        }
        return agent_emojis.get(agent_type, '🤖')

    def _agents_exist(self, force_regenerate=False):
        """
        Check if agent files exist and return missing or to-regenerate agents.
        
        Args:
            force_regenerate (bool): If True, return all agents regardless of existence
            
        Returns:
            list: List of agent types to generate/regenerate
        """
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
        
        if force_regenerate:
            return agent_types
            
        missing_agents = []
        for agent_type in agent_types:
            if not os.path.exists(f".aider.agent.{agent_type}.md"):
                missing_agents.append(agent_type)
                
        return missing_agents
        
    async def _run_single_agent_cycle(self, mission_filepath, model="gpt-4o-mini"):
        """Execute a single cycle for one agent."""
        agent_name = None
        try:
            # Select an unused agent
            agent_name = await self._select_available_agent()
            if not agent_name:
                await asyncio.sleep(1)  # Wait if no agent available
                return
            
            start_time = time.time()
            self.logger.info(f"🕐 Agent {agent_name} starting cycle at {start_time}")
            
            # Execute agent cycle - now properly awaited
            await self._execute_agent_cycle(
                agent_name,
                mission_filepath,
                model
            )
            
            end_time = time.time()
            duration = end_time - start_time
            self.logger.info(f"⏱️ Agent {agent_name} completed cycle in {duration:.2f} seconds")
            
        except Exception as e:
            self.logger.error(f"Error in agent cycle for {agent_name}: {str(e)}")
            raise  # Propagate error to allow agent replacement
            
        finally:
            # Always release agent if it was acquired
            if agent_name:
                async with self._agent_lock:
                    if agent_name in self._active_agents:
                        self._active_agents.remove(agent_name)

    async def _select_available_agent(self):
        """Select an unused agent in a thread-safe way.
        
        This method ensures proper synchronization when selecting agents
        to prevent race conditions in parallel execution.
        
        Returns:
            str: Name of selected agent, or None if no agents available
            
        Thread Safety:
            This method uses asyncio.Lock for thread-safe agent selection
        """
        async with self._agent_lock:
            available_agents = self._get_available_agents()
            unused_agents = [a for a in available_agents if a not in self._active_agents]
            
            if not unused_agents:
                return None
                
            agent_name = random.choice(unused_agents)
            self._active_agents.add(agent_name)
            return agent_name
            
    def _get_folder_context(self, folder_path: str, files: list, subfolders: list, mission_content: str) -> dict:
        """
        Get folder purpose and relationships using GPT.
        
        Args:
            folder_path (str): Path to current folder
            files (list): List of files in folder
            subfolders (list): List of subfolders
            mission_content (str): Overall mission context
            
        Returns:
            dict: Folder context including:
                - purpose: Folder's main purpose
                - relationships: Dict of folder relationships
                    - parent: Relationship with parent folder
                    - siblings: Relationships with sibling folders
                    - children: Relationships with child folders
        """
        if not folder_path:
            raise ValueError("folder_path cannot be empty")
            
        try:
            # Normalize paths
            abs_path = os.path.abspath(folder_path)
            if not self._validate_path_in_project(abs_path):
                raise ValueError(f"Path {folder_path} is outside project directory")
            rel_path = os.path.relpath(abs_path, self.project_root)
            
            # Generate cache key using relative path for consistency
            cache_key = f"{rel_path}:{','.join(sorted(files))}:{','.join(sorted(subfolders))}"
            
            # Check cache first
            if hasattr(self, '_context_cache'):
                cached = self._context_cache.get(cache_key)
                if cached:
                    self.logger.debug(f"Using cached context for {rel_path}")
                    return cached
            else:
                self._context_cache = {}

            # Initialize context with validated paths
            context = {
                'path': abs_path,  # Internal absolute path
                'display_path': rel_path,  # Display relative path
                'purpose': '',
                'relationships': {
                    'parent': 'No parent relationship specified',
                    'siblings': 'No sibling relationships specified',
                    'children': 'No children relationships specified'
                }
            }

            # Create and execute GPT prompt
            prompt = self._create_folder_context_prompt(rel_path, files, subfolders, mission_content)
            self.logger.debug(f"\n🔍 FOLDER CONTEXT PROMPT for {rel_path}:\n{prompt}")
            
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
            
            content = response.choices[0].message.content.strip()
            self.logger.debug(f"\n✨ FOLDER CONTEXT RESPONSE:\n{content}")
            
            # Parse response and update context
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('Purpose:'):
                    context['purpose'] = line.replace('Purpose:', '').strip()
                elif line.startswith('Parent:'):
                    context['relationships']['parent'] = line.replace('Parent:', '').strip()
                elif line.startswith('Siblings:'):
                    context['relationships']['siblings'] = line.replace('Siblings:', '').strip()
                elif line.startswith('Children:'):
                    context['relationships']['children'] = line.replace('Children:', '').strip()
            
            # Validate required fields
            if not context['purpose']:
                context['purpose'] = f"Storage folder for {os.path.basename(rel_path)} content"
                self.logger.warning(f"Generated default purpose for {rel_path}")
                
            # Cache the result
            self._context_cache[cache_key] = context
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get folder context for {rel_path}: {str(e)}")
            raise

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
            files = self._get_folder_files(abs_path)
            subfolders = self._get_subfolders(abs_path)
            
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

    def _get_available_agents(self):
        """List available agents."""
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
        
        return [agent_type for agent_type in agent_types 
                if os.path.exists(f".aider.agent.{agent_type}.md")]
        
    async def _execute_agent_cycle(self, agent_name, mission_filepath, model="gpt-4o-mini"):
        """Execute a single agent cycle."""
        try:
            agent_filepath = f".aider.agent.{agent_name}.md"
            objective_filepath = f".aider.objective.{agent_name}.md"
            
            # Generate objective directly since we're in a thread
            self.objective_manager.generate_objective(
                mission_filepath,
                agent_filepath
            )
            
            # Execute aider operation with model parameter - now properly awaited
            await self.aider_manager.run_aider(
                objective_filepath,
                agent_filepath,
                model=model
            )
                
            self.logger.info(f"✅ Completed execution cycle for {agent_name}")
            
        except Exception as e:
            self.logger.error(f"Error in agent cycle for {agent_name}: {str(e)}")
            raise
            
        finally:
            # Always release agent if it was acquired
            if agent_name:
                async with self._agent_lock:
                    if agent_name in self._active_agents:
                        self._active_agents.remove(agent_name)
