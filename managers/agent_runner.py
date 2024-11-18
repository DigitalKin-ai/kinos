import os
import random
import asyncio
from concurrent.futures import ThreadPoolExecutor
from utils.logger import Logger
from managers.agents_manager import AgentsManager
from managers.objective_manager import ObjectiveManager
from managers.map_manager import MapManager
from managers.aider_manager import AiderManager

class AgentRunner:
    """Runner class for executing and managing agent operations."""
    
    def __init__(self):
        """Initialize the runner with required managers and logger."""
        self.logger = Logger()
        self.agents_manager = AgentsManager()
        self.objective_manager = ObjectiveManager()
        self.map_manager = MapManager()
        self.aider_manager = AiderManager()
        self._running_agents = set()  # Track active agents
        self._agent_lock = asyncio.Lock()  # Synchronize shared resource access
        
    async def run(self, mission_filepath=".aider.mission.md", generate_agents=False, agent_count=5):
        """
        Main execution loop for running agents in parallel.
        
        Args:
            mission_filepath (str): Path to mission specification file
            generate_agents (bool): Whether to generate agents if they don't exist
            agent_count (int): Number of agents to run in parallel
            
        Raises:
            ValueError: If mission file is invalid or agents don't exist
            Exception: For other unexpected errors
        """
        if not self._agents_exist():
            if generate_agents:
                self.logger.info("🔄 Generating agents...")
                self.agents_manager.generate_agents(mission_filepath)
            else:
                raise ValueError("No agents found. Run with --generate flag to generate agents.")

        self.logger.info(f"🚀 Starting {agent_count} agents in parallel")
        
        # Create tasks for each agent
        tasks = []
        for _ in range(agent_count):
            tasks.append(asyncio.create_task(
                self._run_agent_loop(mission_filepath)
            ))
            
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
            
    def _agents_exist(self):
        """Check if agent files exist."""
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
            if not os.path.exists(f".aider.agent.{agent_type}.md"):
                return False
        return True
        
    async def _run_agent_loop(self, mission_filepath):
        """Individual execution loop for each agent."""
        while True:
            try:
                # Select an unused agent
                agent_name = await self._select_available_agent()
                if not agent_name:
                    await asyncio.sleep(1)  # Wait if no agent available
                    continue
                    
                self.logger.info(f"🤖 Agent {agent_name} starting cycle")
                
                # Execute agent cycle
                await self._execute_agent_cycle(agent_name, mission_filepath)
                
                # Release agent
                async with self._agent_lock:
                    self._running_agents.remove(agent_name)
                    
            except Exception as e:
                self.logger.error(f"Error in agent loop: {str(e)}")
                await asyncio.sleep(1)  # Pause before retry

    async def _select_available_agent(self):
        """Select an unused agent in a thread-safe way."""
        async with self._agent_lock:
            available_agents = self._get_available_agents()
            unused_agents = [a for a in available_agents if a not in self._running_agents]
            
            if not unused_agents:
                return None
                
            agent_name = random.choice(unused_agents)
            self._running_agents.add(agent_name)
            return agent_name
            
    def _get_available_agents(self):
        """List available agents."""
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
        
        return [agent_type for agent_type in agent_types 
                if os.path.exists(f".aider.agent.{agent_type}.md")]
        
    async def _execute_agent_cycle(self, agent_name, mission_filepath):
        """Execute a single agent cycle asynchronously."""
        agent_filepath = f".aider.agent.{agent_name}.md"
        objective_filepath = f".aider.objective.{agent_name}.md"
        
        # Use ThreadPoolExecutor for blocking I/O operations
        with ThreadPoolExecutor() as pool:
            # Generate objective
            await asyncio.get_event_loop().run_in_executor(
                pool,
                self.objective_manager.generate_objective,
                mission_filepath,
                agent_filepath
            )
            
            # Generate context map
            map_filepath = f".aider.map.{agent_name}.md"
            await asyncio.get_event_loop().run_in_executor(
                pool,
                self.map_manager.generate_map,
                mission_filepath,
                objective_filepath,
                agent_filepath
            )
            
            # Execute aider operation
            await asyncio.get_event_loop().run_in_executor(
                pool,
                self.aider_manager.run_aider,
                objective_filepath,
                map_filepath,
                agent_filepath
            )
            
        self.logger.info(f"✅ Completed execution cycle for {agent_name}")
