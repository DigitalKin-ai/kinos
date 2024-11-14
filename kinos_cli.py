import sys
import threading
import queue
import time
import random
from cli.commands.commits import commits
from typing import List, Dict
import os
import json
from datetime import datetime
from utils.logger import Logger
from services.agent_service import AgentService

def load_team_config(team_name: str) -> List[str]:
    """Load agent names from team config"""
    try:
        # Use PathManager to get KinOS root path
        from utils.path_manager import PathManager
        kinos_root = PathManager.get_kinos_root()
        
        config_path = os.path.join(kinos_root, "teams", team_name, "config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
            return [agent['name'] if isinstance(agent, dict) else agent 
                   for agent in config.get('agents', [])]
    except Exception as e:
        print(f"Error loading team config: {e}")
        return []

class AgentRunner(threading.Thread):
    """Thread class for running an agent and capturing output"""
    def __init__(self, agent_service: AgentService, team_agents: List[str], 
                 output_queue: queue.Queue, logger: Logger):
        super().__init__(daemon=True)
        self.agent_service = agent_service
        self.team_agents = team_agents
        self.output_queue = output_queue
        self.logger = logger
        self.running = True

    def run(self):
        while self.running:
            try:
                # Capture start time
                start_time = datetime.now()
                
                # Run agent and capture output
                self.agent_service.run_random_agent(self.team_agents)
                
                # Calculate duration
                duration = (datetime.now() - start_time).total_seconds()
                
                # Put completion message in queue
                self.output_queue.put({
                    'thread_id': threading.get_ident(),
                    'status': 'completed',
                    'duration': duration,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.output_queue.put({
                    'thread_id': threading.get_ident(),
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                time.sleep(5)  # Brief pause on error

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
    
    # Create output queue
    output_queue = queue.Queue()
    active_threads: Dict[int, AgentRunner] = {}
    
    try:
        while True:  # Main loop
            # Always try to maintain 2 active threads
            while len(active_threads) < 2:
                # Get current phase weights
                from services import init_services
                services = init_services(None)
                phase_service = services['phase_service']
                phase_status = phase_service.get_status_info()
                current_phase = phase_status['phase']
                phase_weights = phase_service.get_phase_weights(current_phase)
                
                # Filter out agents that are already running
                available_agents = [a for a in agents if not any(
                    runner.agent_name == a for runner in active_threads.values()
                )]
                
                if not available_agents:
                    break
                
                # Get weights for available agents
                weights = [phase_weights.get(agent, 0.5) for agent in available_agents]
                
                # Select random agent based on weights
                agent_name = random.choices(available_agents, weights=weights, k=1)[0]
                
                # Start new runner with selected agent
                runner = AgentRunner(agent_service, [agent_name], output_queue, logger)
                runner.agent_name = agent_name  # Store selected agent name
                runner.start()
                active_threads[runner.ident] = runner
                logger.log(f"Started new agent runner for {agent_name} (total: {len(active_threads)})")

            try:
                # Check queue for messages with timeout
                try:
                    msg = output_queue.get(timeout=0.1)
                    thread_id = msg['thread_id']
                    
                    # Log message based on status
                    if msg['status'] == 'completed':
                        logger.log(
                            f"Agent {active_threads[thread_id].agent_name} completed "
                            f"(duration: {msg['duration']:.1f}s)", 
                            'success'
                        )
                    elif msg['status'] == 'error':
                        logger.log(
                            f"Agent {active_threads[thread_id].agent_name} error: {msg['error']}", 
                            'error'
                        )
                    
                    # Remove completed/failed thread
                    if thread_id in active_threads:
                        active_threads[thread_id].running = False
                        del active_threads[thread_id]
                        
                except queue.Empty:
                    pass  # No messages
                    
            except KeyboardInterrupt:
                raise  # Re-raise to outer try
                
            except Exception as e:
                logger.log(f"Error processing agent output: {str(e)}", 'error')
                
            # Brief sleep to prevent CPU spinning
            time.sleep(0.1)
                
    except KeyboardInterrupt:
        logger.log("Stopping team execution...")
        
        # Stop all threads
        for runner in active_threads.values():
            runner.running = False
            
        # Wait for threads to finish
        for runner in active_threads.values():
            runner.join(timeout=1.0)
            
def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: kin <command>")
        return

    command = sys.argv[1]
    
    if command == "commits":
        if len(sys.argv) < 3:
            print("Usage: kin commits <generate>")
            return
        if sys.argv[2] == "generate":
            from utils.generate_commit_log import generate_commit_log
            generate_commit_log()
    else:
        # Execute team command
        team_name = command
        run_team_loop(team_name)

if __name__ == "__main__":
    main()
