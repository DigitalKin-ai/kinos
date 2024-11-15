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
                # Capture start time
                start_time = datetime.now()
            
                # Enhanced logging
                self.logger.log(f"Running agent: {self.team_agents}", 'debug')
            
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
                    'traceback': traceback.format_exc(),
                    'timestamp': datetime.now().isoformat()
                })
            
                # Log detailed error
                self.logger.log(
                    f"Agent runner error:\n{traceback.format_exc()}",
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
    
    # RESEARCH AGENT DETECTION LIST
    research_agents = [
        'management', 'specifications', 'chercheur', 
        'evaluation', 'chroniqueur', 'documentaliste', 
        'duplication', 'redondance', 'validation', 'redacteur'
    ]
    
    try:
        while True:  # Main loop
            logger.log("Checking agent initialization conditions", 'debug')
            
            # Always try to maintain several active threads
            while True:  # Main loop
                # Clean up finished threads
                active_threads = {tid: runner for tid, runner in active_threads.items() 
                                if runner.is_alive()}
                
                # Start new threads if needed
                while len(active_threads) < 2:
                    # Get current phase weights with logging
                    from services import init_services
                    services = init_services(None)
                    phase_service = services['phase_service']
                    phase_status = phase_service.get_status_info()
                    current_phase = phase_status['phase']
                
                    logger.log(f"Current project phase: {current_phase}", 'debug')
                
                    phase_weights = phase_service.get_phase_weights(current_phase)
                    logger.log(f"Phase weights: {phase_weights}", 'debug')
                
                    # Filter out agents that are already running
                    available_agents = [a for a in agents if not any(
                        runner.agent_name == a for runner in active_threads.values()
                    )]
                    
                    if not available_agents:
                        time.sleep(1)  # Wait if all agents are busy
                        break  # Exit inner loop to clean up threads again
                
                # Get weights for available agents
                weights = [phase_weights.get(agent, 0.5) for agent in available_agents]
                
                # Select random agent based on weights
                agent_name = random.choices(available_agents, weights=weights, k=1)[0]
                
                # COMPREHENSIVE AGENT TYPE DETECTION
                agent_type = 'aider'  # Default type
                
                # 1. Check research agents list (highest priority)
                if agent_name.lower() in [a.lower() for a in research_agents]:
                    agent_type = 'research'
                    logger.log(
                        f"Agent {agent_name} explicitly set to research type "
                        f"(matched research agents list)", 
                        'debug'
                    )
                
                # 2. Check team configuration
                for team in services['team_service'].predefined_teams:
                    for agent in team.get('agents', []):
                        if isinstance(agent, dict) and agent['name'] == agent_name:
                            # Override type from team config if specified
                            detected_type = agent.get('type', 'aider').lower()
                            if detected_type != agent_type:
                                logger.log(
                                    f"Agent {agent_name} type updated from {agent_type} "
                                    f"to {detected_type} (team config)", 
                                    'debug'
                                )
                                agent_type = detected_type
                            break
                
                # 3. Validate and normalize agent type
                if agent_type not in ['aider', 'research']:
                    agent_type = 'aider'
                    logger.log(
                        f"Agent {agent_name} type normalized to 'aider'", 
                        'debug'
                    )
                
                # Detailed logging for agent launch
                logger.log(
                    f"🚀 Launching agent: {agent_name}\n"
                    f"  Phase: {current_phase}\n"
                    f"  Weight: {phase_weights.get(agent_name, 0.5):.2f}\n"
                    f"  Type: {agent_type}\n"
                    f"  Available agents: {', '.join(available_agents)}", 
                    'info'
                )
                
                # Start new runner with selected agent
                runner = AgentRunner(agent_service, [agent_name], output_queue, logger)
                runner.agent_name = agent_name  # Store selected agent name
                runner.agent_type = agent_type  # Store agent type
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
