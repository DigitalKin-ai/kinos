import sys
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
            manager.generate_agents(mission_path)
            
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
            sys.exit(1)
            
        subcommand = sys.argv[2]
        if subcommand == "agents":
            runner = AgentRunner()
            # Optional mission file path
            mission_path = sys.argv[3] if len(sys.argv) > 3 else ".aider.mission.md"
            runner.run(mission_path)
            
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
