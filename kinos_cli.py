import sys
import threading
import queue
import time
import random
import argparse
import traceback
from cli.commands.commits import commits
from typing import List, Dict
import os
import json
from datetime import datetime
from utils.logger import Logger
from services.agent_service import AgentService
from utils.model_router import ModelRouter

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
        self.agent_name = None
        self.agent_type = 'aider'  # Default type

    def run(self):
        while self.running:
            try:
                # Log start of agent execution
                self.logger.log(f"Starting agent execution: {self.agent_name}", 'debug')
                
                # Capture start time
                start_time = datetime.now()
            
                # Run agent with explicit logging
                self.logger.log(f"Running agent {self.agent_name} with team agents: {self.team_agents}", 'debug')
                
                # Initialize agent
                agent = self.agent_service.create_agent(self.agent_name)
                if not agent:
                    self.logger.log(f"Failed to create agent: {self.agent_name}", 'error')
                    continue
                    
                self.logger.log(f"Agent {self.agent_name} created successfully", 'debug')
                
                # Start agent
                try:
                    agent.start()
                    self.logger.log(f"Agent {self.agent_name} started", 'debug')
                except Exception as start_error:
                    self.logger.log(f"Error starting agent {self.agent_name}: {str(start_error)}", 'error')
                    continue
                
                # Run agent's main loop
                try:
                    agent.run()
                except Exception as run_error:
                    self.logger.log(f"Error in agent {self.agent_name} run loop: {str(run_error)}", 'error')
                
                # Calculate duration
                duration = (datetime.now() - start_time).total_seconds()
            
                # Put completion message in queue
                self.output_queue.put({
                    'thread_id': threading.get_ident(),
                    'agent_name': self.agent_name,
                    'status': 'completed',
                    'duration': duration,
                    'timestamp': datetime.now().isoformat()
                })
            
            except Exception as e:
                self.output_queue.put({
                    'thread_id': threading.get_ident(),
                    'agent_name': self.agent_name,
                    'status': 'error',
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                    'timestamp': datetime.now().isoformat()
                })
            
                # Log detailed error
                self.logger.log(
                    f"Agent runner error for {self.agent_name}:\n{traceback.format_exc()}",
                    'error'
                )
            
                time.sleep(5)  # Brief pause on error

def run_team_loop(team_name: str):
    """Main team execution loop"""
    logger = Logger()
    logger.log(f"🚀 Starting team loop for: {team_name}", 'debug')
    
    agent_service = AgentService(None)
    
    # Load team configuration with enhanced logging
    agents = load_team_config(team_name)
    logger.log(f"Loaded {len(agents)} agents: {', '.join(agents)}", 'debug')
    
    if not agents:
        logger.log(f"No agents found for team: {team_name}", 'error')
        return
        
    logger.log(f"Starting team {team_name} with agents: {', '.join(agents)}")
    
    # Create output queue
    output_queue = queue.Queue()
    active_threads: Dict[int, AgentRunner] = {}
    
    logger.log("Entering main loop", 'debug')
    
    try:
        while True:  # Main loop
            logger.log("Checking agent initialization conditions", 'debug')
            
            # Clean up finished threads
            active_threads = {tid: runner for tid, runner in active_threads.items() 
                            if runner.is_alive()}
            
            logger.log(f"Active threads: {len(active_threads)}", 'debug')
            
            # Start new threads if needed
            while len(active_threads) < 3:
                # Get current phase weights
                from services import init_services
                services = init_services(None)
                phase_service = services['phase_service']
                phase_status = phase_service.get_status_info()
                current_phase = phase_status['phase']
                
                logger.log(f"Current phase: {current_phase}", 'debug')
                
                phase_weights = phase_service.get_phase_weights(current_phase)
                logger.log(f"Phase weights: {phase_weights}", 'debug')
                
                # Filter available agents
                available_agents = [a for a in agents if not any(
                    runner.agent_name == a for runner in active_threads.values()
                )]
                
                if not available_agents:
                    logger.log("No available agents, waiting...", 'debug')
                    time.sleep(1)
                    break
                
                # Get weights for available agents
                weights = [phase_weights.get(agent, 0.5) for agent in available_agents]
                
                # Select random agent based on weights
                agent_name = random.choices(available_agents, weights=weights, k=1)[0]
                
                logger.log(f"Selected agent: {agent_name}", 'debug')
                
                # Start new runner
                runner = AgentRunner(agent_service, [agent_name], output_queue, logger)
                runner.agent_name = agent_name
                runner.start()
                active_threads[runner.ident] = runner
                logger.log(f"Started new agent runner for {agent_name} (total: {len(active_threads)})")
            
            # Process output queue
            try:
                msg = output_queue.get(timeout=0.1)
                logger.log(f"Received message from queue: {msg['status']}", 'warning')
            except queue.Empty:
                pass
            
            time.sleep(0.1)  # Brief sleep to prevent CPU spinning
                
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
    # Configure parser
    parser = argparse.ArgumentParser(description='KinOS CLI')
    parser.add_argument('command', help='Command to execute')
    parser.add_argument('--model', help='Model to use (e.g. "claude-3-haiku", "gpt-4", etc.)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    # Configure logger for debug logs if verbose
    logger = Logger()
    if args.verbose:
        logger.set_level('debug')

    # If model is specified, update ModelRouter
    if args.model:
        try:
            from services import init_services
            services = init_services(None)
            model_router = services['model_router']
                    
            if not model_router.set_model(args.model):
                logger.log(f"Model {args.model} not found. Available models:", 'warning')
                for provider, models in model_router.get_available_models().items():
                    logger.log(f"{provider}: {', '.join(models)}", 'info')
                return
                        
        except Exception as e:
            logger.log(f"Error setting model: {str(e)}", 'error')
            return

    if args.command == "commits":
        if len(sys.argv) < 3:
            print("Usage: kin commits <generate>")
            return
        if sys.argv[2] == "generate":
            from utils.generate_commit_log import generate_commit_log
            generate_commit_log()
    else:
        # Execute team command
        team_name = args.command
        run_team_loop(team_name)

if __name__ == "__main__":
    main()
