import sys
import logging
import asyncio
from managers.agents_manager import AgentsManager
from managers.objective_manager import ObjectiveManager
from managers.map_manager import MapManager
from managers.aider_manager import AiderManager
from managers.agent_runner import AgentRunner

def main():
    if len(sys.argv) < 2:
        print("Usage: kin <command> [options]")
        sys.exit(1)

    command = sys.argv[1]
    
    # Route commands to appropriate managers
    if command == "generate":
        if len(sys.argv) < 3:
            print("Usage: kin generate <agents|objective|map> [options]")
            sys.exit(1)
            
        subcommand = sys.argv[2]
        if subcommand == "agents":
            manager = AgentsManager()
            # Optional mission file path
            mission_path = sys.argv[3] if len(sys.argv) > 3 else ".aider.mission.md"
            asyncio.run(manager.generate_agents(mission_path))
            
        elif subcommand == "objective":
            manager = ObjectiveManager()
            
            # Parse arguments
            if len(sys.argv) < 4 or sys.argv[3] != "--agent":
                print("Usage: kin generate objective --agent <agent_name>")
                sys.exit(1)
                
            if len(sys.argv) < 5:
                print("Usage: kin generate objective --agent <agent_name>")
                sys.exit(1)
                
            agent_name = sys.argv[4]
            agent_path = f".aider.agent.{agent_name}.md"
            mission_path = ".aider.mission.md"
            
            manager.generate_objective(mission_path, agent_path)
            
        elif subcommand == "map":
            manager = MapManager()
            
            # Parse arguments
            if len(sys.argv) < 4 or sys.argv[3] != "--agent":
                print("Usage: kin generate map --agent <agent_name>")
                sys.exit(1)
                
            if len(sys.argv) < 5:
                print("Usage: kin generate map --agent <agent_name>")
                sys.exit(1)
                
            agent_name = sys.argv[4]
            agent_path = f".aider.agent.{agent_name}.md"
            objective_path = f".aider.objective.{agent_name}.md"
            mission_path = ".aider.mission.md"
            
            manager.generate_map(mission_path, objective_path, agent_path)
            
    elif command == "run":
        if len(sys.argv) < 3:
            print("Usage: kin run <agents|aider> [options]")
            print("Options:")
            print("  --generate    Generate agents if missing")
            print("  --verbose     Show detailed debug information")
            print("  --mission     Specify mission file path")
            sys.exit(1)
            
        subcommand = sys.argv[2]
        if subcommand == "agents":
            # Create and initialize runner asynchronously
            async def init_and_run_agents():
                runner = await AgentRunner()  # Await the initialization
                
                # Set default log level to SUCCESS (only show success and above)
                runner.logger.logger.setLevel(logging.SUCCESS)
                
                # Check for --verbose flag
                if "--verbose" in sys.argv:
                    runner.logger.logger.setLevel(logging.DEBUG)
                    
                # Get mission file path
                mission_path = ".aider.mission.md"  # default
                if "--mission" in sys.argv:
                    try:
                        mission_index = sys.argv.index("--mission") + 1
                        if mission_index < len(sys.argv):
                            mission_path = sys.argv[mission_index]
                    except (ValueError, IndexError):
                        print("Missing value for --mission flag")
                        sys.exit(1)
                    
                # Get agent count
                agent_count = 10  # Default value
                if "--count" in sys.argv:
                    try:
                        count_index = sys.argv.index("--count") + 1
                    agent_count = int(sys.argv[count_index])
                    except (ValueError, IndexError):
                        print("Invalid value for --count. Using default (10)")
                
                # Check for --generate flag    
                should_generate = "--generate" in sys.argv
                
                # Afficher le message de démarrage
                runner.logger.success("🌟 Lancement du KinOS...")

                # Run with the initialized runner
                await runner.run(
                    mission_path, 
                    generate_agents=should_generate,
                    agent_count=agent_count
                )

            # Run the async initialization and execution
            asyncio.run(init_and_run_agents())
            
        elif subcommand == "aider":
            manager = AiderManager()
            
            # Parse arguments
            if len(sys.argv) < 4 or sys.argv[3] != "--agent":
                print("Usage: kin run aider --agent <agent_name>")
                sys.exit(1)
                
            if len(sys.argv) < 5:
                print("Usage: kin run aider --agent <agent_name>")
                sys.exit(1)
                
            agent_name = sys.argv[4]
            
            # Use default paths based on agent name
            agent_path = f".aider.agent.{agent_name}.md"
            objective_path = f".aider.objective.{agent_name}.md"  # Default objective path
            map_path = f".aider.map.{agent_name}.md"  # Default map path
            
            manager.run_aider(
                objective_filepath=objective_path,
                map_filepath=map_path,
                agent_filepath=agent_path
            )
            
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
