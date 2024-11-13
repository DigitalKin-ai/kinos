import sys
import threading
import time
from typing import List
import os
import json
from utils.logger import Logger
from services.agent_service import AgentService

def load_team_config(team_name: str) -> List[str]:
    """Load agent names from team config"""
    try:
        config_path = os.path.join("teams", team_name, "config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
            return [agent['name'] if isinstance(agent, dict) else agent 
                   for agent in config.get('agents', [])]
    except Exception as e:
        print(f"Error loading team config: {e}")
        return []

def run_team_loop(team_name: str):
    """Main team execution loop"""
    logger = Logger()
    agent_service = AgentService(None)
    
    # Load team configuration
    agents = load_team_config(team_name)
    if not agents:
        logger.log(f"No agents found for team: {team_name}", 'error')
        return
        
    logger.log(f"Starting team {team_name} with agents: {', '.join(agents)}")
    
    # Create thread pool
    threads = []
    
    try:
        while True:  # Main loop
            # Start 3 agent runs in parallel
            while len(threads) < 3:
                thread = threading.Thread(
                    target=agent_service.run_random_agent,
                    args=(agents,),
                    daemon=True
                )
                thread.start()
                threads.append(thread)
            
            # Wait for any thread to finish
            while threads:
                for thread in threads[:]:
                    if not thread.is_alive():
                        threads.remove(thread)
                        # Start new thread if removed one
                        if len(threads) < 3:
                            new_thread = threading.Thread(
                                target=agent_service.run_random_agent,
                                args=(agents,),
                                daemon=True
                            )
                            new_thread.start()
                            threads.append(new_thread)
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        logger.log("Stopping team execution...")
        # Wait for current threads to finish
        for thread in threads:
            thread.join(timeout=1.0)

def main():
    """CLI entry point"""
    if len(sys.argv) != 2:
        print("Usage: kin <team_name>")
        return
        
    team_name = sys.argv[1]
    run_team_loop(team_name)

if __name__ == "__main__":
    main()
