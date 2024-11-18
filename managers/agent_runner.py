import os
import random
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
        
    def run(self, mission_filepath=".aider.mission.md", generate_agents=False):
        """
        Main execution loop for running agents.
        
        Args:
            mission_filepath (str): Path to mission specification file
            generate_agents (bool): Whether to generate agents if they don't exist
            
        Raises:
            ValueError: If mission file is invalid or agents don't exist
            Exception: For other unexpected errors
        """
        # 1. Verify/generate agents
        if not self._agents_exist():
            if generate_agents:
                self.logger.info("🔄 Generating agents...")
                self.agents_manager.generate_agents(mission_filepath)
            else:
                raise ValueError("No agents found. Run with --generate flag to generate agents.")
        
        # 2. Main execution loop
        while True:
            # Select random agent
            agent_name = self._select_random_agent()
            if not agent_name:
                raise ValueError("No agents available")
                
            self.logger.info(f"🤖 Selected agent: {agent_name}")
            
            # Execute agent cycle - let exceptions propagate
            self._execute_agent_cycle(agent_name, mission_filepath)
            
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
        
    def _select_random_agent(self):
        """Randomly select an available agent."""
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
        
        available_agents = []
        for agent_type in agent_types:
            if os.path.exists(f".aider.agent.{agent_type}.md"):
                available_agents.append(agent_type)
                
        return random.choice(available_agents) if available_agents else None
        
    def _execute_agent_cycle(self, agent_name, mission_filepath):
        """
        Execute a single agent cycle.
        
        Args:
            agent_name (str): Name of the selected agent
            mission_filepath (str): Path to mission file
        """
        # 1. Generate new objective
        agent_filepath = f".aider.agent.{agent_name}.md"
        objective_filepath = f".aider.objective.{agent_name}.md"
        self.objective_manager.generate_objective(
            mission_filepath=mission_filepath,
            agent_filepath=agent_filepath
        )
        
        # 2. Generate context map
        map_filepath = f".aider.map.{agent_name}.md"
        self.map_manager.generate_map(
            mission_filepath=mission_filepath,
            objective_filepath=objective_filepath,
            agent_filepath=agent_filepath
        )
        
        # 3. Execute aider operation
        self.aider_manager.run_aider(
            objective_filepath=objective_filepath,
            map_filepath=map_filepath,
            agent_filepath=agent_filepath
        )
        
        self.logger.info(f"✅ Completed execution cycle for {agent_name}")
