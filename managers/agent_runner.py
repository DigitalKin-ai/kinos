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
        """
        try:
            # First validate mission file
            if not os.path.exists(mission_filepath):
                self.logger.error("❌ Fichier de mission introuvable!")
                self.logger.info("\n📋 Pour démarrer KinOS, vous devez :")
                self.logger.info("   1. Soit créer un fichier '.aider.mission.md' dans le dossier courant")
                self.logger.info("   2. Soit spécifier le chemin vers votre fichier de mission avec --mission")
                self.logger.info("\n💡 Exemples :")
                self.logger.info("   kin run agents --generate")
                self.logger.info("   kin run agents --generate --mission chemin/vers/ma_mission.md")
                self.logger.info("\n📝 Le fichier de mission doit contenir la description de votre projet.")
                raise SystemExit(1)

            # Then check for missing agents
            missing_agents = self._agents_exist()
            if missing_agents:
                if generate_agents:
                    self.logger.info("🔄 Génération des agents...")
                    self.agents_manager.generate_agents(mission_filepath)
                else:
                    self.logger.error("❌ Agents manquants détectés!")
                    self.logger.info("\n🤖 Les agents suivants sont requis mais n'ont pas été trouvés:")
                    for agent in missing_agents:
                        self.logger.info(f"   • {self._get_agent_emoji(agent)} Agent {agent}")
                    self.logger.info("\n💡 Pour générer les agents manquants, utilisez la commande:")
                    self.logger.info("   kin run agents --generate")
                    self.logger.info("\n📝 Ou spécifiez un fichier de mission différent avec --mission")
                    raise SystemExit(1)

            self.logger.info(f"🚀 Démarrage avec {agent_count} agents en parallèle")
        except Exception as e:
            self.logger.error(f"Error during initialization: {str(e)}")
            raise

        # Create initial pool of agents with delay between starts
        tasks = set()
        for i in range(agent_count):
            await asyncio.sleep(5)  # 5 second delay between each start
            tasks.add(asyncio.create_task(
                self._run_single_agent_cycle(mission_filepath)
            ))
        
        # Maintain active agent count
        while True:
            # Wait for an agent to complete
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            
            # Handle completed agents
            for task in done:
                try:
                    await task  # Get potential errors
                except Exception as e:
                    self.logger.error(f"Agent task failed: {str(e)}")
                
                # Create new agent to replace completed one
                await asyncio.sleep(3)  # Delay before starting new agent
                tasks.add(asyncio.create_task(
                    self._run_single_agent_cycle(mission_filepath)
                ))
            
            # Update pending tasks
            tasks = pending
            
    def _get_agent_emoji(self, agent_type):
        """Get the appropriate emoji for an agent type."""
        agent_emojis = {
            'specification': '📌',
            'management': '🧭',
            'redaction': '✍️',
            'evaluation': '⚖️',
            'duplication': '👥',
            'chroniqueur': '📜',
            'redondance': '🎭',
            'production': '🏭'
        }
        return agent_emojis.get(agent_type, '🤖')

    def _agents_exist(self):
        """Check if agent files exist and return missing agents."""
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
        
        missing_agents = []
        for agent_type in agent_types:
            if not os.path.exists(f".aider.agent.{agent_type}.md"):
                missing_agents.append(agent_type)
                
        return missing_agents
        
    async def _run_single_agent_cycle(self, mission_filepath):
        """Execute a single cycle for one agent."""
        try:
            # Select an unused agent
            agent_name = await self._select_available_agent()
            if not agent_name:
                await asyncio.sleep(1)  # Wait if no agent available
                return
                
            self.logger.info(f"🤖 Agent {agent_name} starting cycle")
            
            # Execute agent cycle
            await self._execute_agent_cycle(agent_name, mission_filepath)
            
            # Release agent
            async with self._agent_lock:
                self._running_agents.remove(agent_name)
                
        except Exception as e:
            self.logger.error(f"Error in agent cycle: {str(e)}")
            raise  # Propagate error to allow agent replacement

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
