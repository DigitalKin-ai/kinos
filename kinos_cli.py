import sys
import threading
import queue
import time
import random
import argparse
import traceback
from cli.commands.commits import commits
from typing import List, Dict, Optional
import os
import json
from datetime import datetime
from utils.logger import Logger
from agents.aider.aider_agent import AiderAgent
from services.team_service import TeamService
from utils.model_router import ModelRouter
from utils.path_manager import PathManager

def load_team_config(team_name: str) -> List[str]:
    """Load agent names from team config"""
    try:
        # Use PathManager to get team path
        team_path = os.path.join(os.getcwd(), f"team_{team_name}")
        config_path = os.path.join(team_path, "config.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                return [agent['name'] if isinstance(agent, dict) else agent 
                       for agent in config.get('agents', [])]
        return []
        
    except Exception as e:
        print(f"Error loading team config: {e}")
        return []

class AgentRunner(threading.Thread):
    """Thread class for running an agent and capturing output"""
    _active_runners = {}  # Dict to track {agent_key: thread_id}
    _runner_lock = threading.Lock()
    LOCK_TIMEOUT = 5.0  # 5 second timeout for lock acquisition

    @classmethod
    def is_agent_running(cls, agent_name: str, team_name: str) -> bool:
        """Check if an agent is already running"""
        agent_key = f"{agent_name}_{team_name}"
        try:
            if not cls._runner_lock.acquire(timeout=cls.LOCK_TIMEOUT):
                raise TimeoutError("Timeout waiting for runner lock")
            try:
                if agent_key in cls._active_runners:
                    thread_id = cls._active_runners[agent_key]
                    for thread in threading.enumerate():
                        if thread.ident == thread_id and thread.is_alive():
                            return True
                    del cls._active_runners[agent_key]
                return False
            finally:
                cls._runner_lock.release()
        except TimeoutError:
            print(f"Lock timeout in is_agent_running for {agent_key}")
            return False

    def __init__(self, team_agents: List[str], output_queue: queue.Queue, logger: Logger, team_name: str):
        """Initialize agent runner with comprehensive error handling"""
        try:
            self.logger = logger
            self.logger.log("[AgentRunner] Starting initialization", 'debug')
            
            # Validate inputs before lock
            if not team_agents:
                raise ValueError("No agents specified")
            if not team_name:
                raise ValueError("Team name is required")
                
            agent_name = team_agents[0]
            self.logger.log(f"[AgentRunner] Initializing for agent: {agent_name}", 'debug')
            
            agent_key = f"{agent_name}_{team_name}"
            self.logger.log(f"[AgentRunner] Agent key: {agent_key}", 'debug')

            # Initialize thread first
            self.logger.log("[AgentRunner] Initializing thread", 'debug')
            super().__init__(daemon=True)
            
            # Set basic attributes
            self.logger.log("[AgentRunner] Setting basic attributes", 'debug')
            self.team_agents = team_agents
            self.output_queue = output_queue
            self.running = True
            self.agent_type = 'aider'
            self.team_name = team_name
            self.agent_config = None
            self._agent_key = agent_key

            # Critical section - just for runner registration
            self.logger.log("[AgentRunner] Attempting to acquire runner lock", 'debug')
            if not self._runner_lock.acquire(timeout=self.LOCK_TIMEOUT):
                raise TimeoutError(f"Timeout waiting for runner lock during initialization of {agent_key}")
            
            try:
                self.logger.log("[AgentRunner] Checking for existing runner", 'debug')
                if self.is_agent_running(agent_name, team_name):
                    error_msg = f"Runner for agent {agent_name} already exists in team {team_name}"
                    self.logger.log(f"[AgentRunner] {error_msg}", 'error')
                    raise RuntimeError(error_msg)
                
                self.logger.log("[AgentRunner] Registering runner", 'debug')
                self._active_runners[agent_key] = threading.current_thread().ident
            finally:
                self.logger.log("[AgentRunner] Releasing runner lock", 'debug')
                self._runner_lock.release()
            
            self.logger.log(f"[AgentRunner] Initialization complete for {agent_name} in team {team_name}", 'debug')
                
        except Exception as e:
            error_msg = f"[AgentRunner] Critical error during initialization: {str(e)}\n{traceback.format_exc()}"
            if hasattr(self, 'logger'):
                self.logger.log(error_msg, 'error')
            else:
                print(error_msg)  # Fallback if logger isn't set
            raise

    def run(self):
        """Thread execution loop with enhanced error handling"""
        try:
            self.logger.log(f"[AgentRunner] Starting run loop for team {self.team_name}", 'debug')
            
            while self.running:
                try:
                    if not self.agent_config:
                        self.logger.log("[AgentRunner] Waiting for agent config...", 'debug')
                        time.sleep(5)
                        continue
                        
                    self.logger.log("[AgentRunner] Creating agent instance", 'debug')
                    agent = AiderAgent(self.agent_config)
                    
                    if not agent:
                        self.logger.log("[AgentRunner] Failed to create agent instance", 'error')
                        time.sleep(5)
                        continue
                    
                    self.logger.log("[AgentRunner] Agent instance created successfully", 'debug')
                    
                    max_runtime = 300
                    start = time.time()
                    
                    while time.time() - start < max_runtime and self.running:
                        self.logger.log("[AgentRunner] Running agent iteration", 'debug')
                        agent.run()
                        time.sleep(1)
                        
                    agent.cleanup()
                    self.logger.log("[AgentRunner] Agent cleanup completed", 'debug')
                    
                    time.sleep(random.uniform(5, 15))
                    
                except Exception as e:
                    error_msg = f"[AgentRunner] Error in run loop: {str(e)}\n{traceback.format_exc()}"
                    self.logger.log(error_msg, 'error')
                    self.output_queue.put({
                        'thread_id': threading.get_ident(),
                        'agent_name': self.agent_config['name'] if self.agent_config else 'unknown',
                        'status': 'error',
                        'error': str(e),
                        'traceback': traceback.format_exc(),
                        'timestamp': datetime.now().isoformat()
                    })
                    time.sleep(5)
                    
        except Exception as e:
            error_msg = f"[AgentRunner] Critical error in run method: {str(e)}\n{traceback.format_exc()}"
            self.logger.log(error_msg, 'error')
        finally:
            self.cleanup()
            self.logger.log("[AgentRunner] Thread cleanup completed", 'debug')

    def cleanup(self):
        """Remove agent from active runners"""
        if self._agent_key:
            with self._runner_lock:
                if self._agent_key in self._active_runners:
                    del self._active_runners[self._agent_key]
                    self.logger.log(f"[AgentRunner] Removed {self._agent_key} from active runners", 'debug')

def initialize_team_structure(team_name: str, specific_name: str = None):
    """
    Initialize team directory structure
    
    Args:
        team_name: Name of the team
        specific_name: Optional specific agent name
    """
    logger = Logger()
    
    # Create team directory with "team_" prefix if not already present
    team_dir_name = f"team_{team_name}" if not team_name.startswith("team_") else team_name
    team_dir = os.path.join(os.getcwd(), team_dir_name)
    
    # Create subdirectories
    subdirs = ['history', 'prompts']
    for subdir in subdirs:
        os.makedirs(os.path.join(team_dir, subdir), exist_ok=True)
    
    # Default files with their content - map.md directly in team directory
    default_files = {
        'map.md': '# Project Map\n\n## Overview\n',  # Place map.md in team root
        'todolist.md': '# Todo List\n\n## Pending Tasks\n',
        'demande.md': '# Mission Request\n\n## Objective\n',
        'directives.md': '# Project Directives\n\n## Guidelines\n'
    }
    
    # Create default files in team directory
    for filename, content in default_files.items():
        file_path = os.path.join(team_dir, filename)
        
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.log(f"Created {filename} in {team_dir_name}", 'info')
    
    # Create .gitignore in team directory
    gitignore_path = os.path.join(team_dir, '.gitignore')
    gitignore_content = """# Ignore Aider and KinOS history files
.DS_Store
.vscode/
aider.code-workspace
*.pyc
.aider*
.kinos*
*/agents/*
aider_chat.egg-info/
build
dist/
Gemfile.lock
_site
.jekyll-cache/
.jekyll-metadata
aider/__version__.py
.venv/
"""
    
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    logger.log(f"Created .gitignore in {team_dir_name}", 'info')
    
    # Create team config file
    config_path = os.path.join(team_dir, 'config.json')
    
    # Configuration par défaut
    kinos_config = {
        "name": team_name,
        "type": "book_writing",
        "paths": {
            "prompts": os.path.join(team_dir, "prompts"),
            "history": os.path.join(team_dir, "history")
        },
        "created_at": datetime.now().isoformat()
    }
    
    # Write config file
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(kinos_config, f, indent=2)
    
    logger.log(f"Created config.json in {team_dir_name}", 'info')

def run_team_loop(team_name: str, specific_name: str = None):
    """Main team execution loop"""
    logger = Logger()
    logger.log(f"🚀 Starting team loop for: {team_name}", 'debug')
    
    # Initialiser la structure de l'équipe
    initialize_team_structure(team_name, specific_name)

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
            
            # Start new threads if needed
            while len(active_threads) <1:
                # Select random agent
                agent_name = random.choice(agents)
                
                logger.log(f"Selected agent: {agent_name}", 'debug')
                
                # Start new runner
                runner = AgentRunner(agents, output_queue, logger, team_name)
                runner.start()
                active_threads[runner.ident] = runner
                logger.log(f"Started new agent runner (total: {len(active_threads)})")
            
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
            
def run_multi_team_loop(model: Optional[str] = None):
    """Run agents by finding and using random prompts from all prompts folders"""
    logger = Logger()
    logger.log("🌐 Starting multi-team prompt-based execution", 'debug')
    
    try:
        # Initialize services once at startup
        from services import init_services
        services = init_services(None)
        
        # Set model if specified and validate it exists
        if model:
            model_router = services['model_router']
            if not model_router.set_model(model):
                logger.log(f"Model {model} not found or unavailable", 'error')
                return
            logger.log(f"Using model: {model}", 'info')
        else:
            logger.log("No model specified, using default", 'warning')

        # Create output queue and active threads dict
        output_queue = queue.Queue()
        active_threads: Dict[int, AgentRunner] = {}
        MAX_AGENTS = 5

        while True:
            try:
                # Clean up finished threads
                active_threads = {tid: runner for tid, runner in active_threads.items() 
                                if runner.is_alive()}
                logger.log(f"Active threads: {len(active_threads)}", 'debug')
                
                # Find all team directories first
                team_dirs = []
                for item in os.listdir(os.getcwd()):
                    if os.path.isdir(item) and item.startswith('team_'):
                        team_dir = os.path.join(os.getcwd(), item)
                        prompts_dir = os.path.join(team_dir, 'prompts')
                        if os.path.exists(prompts_dir):
                            team_dirs.append(team_dir)

                if not team_dirs:
                    logger.log("No team directories found", 'warning')
                    time.sleep(10)
                    continue

                logger.log(f"Found {len(team_dirs)} team directories", 'debug')

                # Start new threads if needed
                while len(active_threads) < MAX_AGENTS:
                    try:
                        # Select random team and prompt
                        team_dir = random.choice(team_dirs)
                        team_name = os.path.basename(team_dir).replace('team_', '')
                        logger.log(f"Selected team directory: {team_dir}", 'debug')
                        
                        prompts_dir = os.path.join(team_dir, 'prompts')
                        if not os.path.exists(prompts_dir):
                            logger.log(f"No prompts directory found for team {team_name}", 'warning')
                            continue
                            
                        prompts = [f for f in os.listdir(prompts_dir) if f.endswith('.md')]
                        if not prompts:
                            logger.log(f"No prompt files found in {prompts_dir}", 'warning')
                            continue

                        logger.log(f"Found {len(prompts)} prompts for team {team_name}", 'debug')
                        prompt_file = random.choice(prompts)
                        agent_name = os.path.splitext(os.path.basename(prompt_file))[0]
                        logger.log(f"Selected prompt: {prompt_file} for agent: {agent_name}", 'debug')

                        # Check if agent is already running
                        if AgentRunner.is_agent_running(agent_name, team_name):
                            logger.log(f"Agent {agent_name} already running for team {team_name}", 'debug')
                            continue

                        # Create agent config with detailed logging
                        try:
                            agent_config = {
                                'name': agent_name,
                                'team': team_name,
                                'type': 'aider',
                                'mission_dir': team_dir,
                                'prompt_file': os.path.join(prompts_dir, prompt_file),
                                'weight': 0.5,
                                'services': services
                            }
                            logger.log(f"Created agent config: {agent_config}", 'debug')

                            # Create and start new runner with error handling
                            try:
                                logger.log(f"Creating runner for {agent_name} in team {team_name}", 'debug')
                                runner = AgentRunner([agent_name], output_queue, logger, team_name)
                                logger.log("Runner created successfully", 'debug')
                                
                                logger.log("Setting agent config", 'debug')
                                runner.agent_config = agent_config
                                
                                logger.log("Starting runner thread", 'debug')
                                runner.start()
                                logger.log("Runner thread started successfully", 'debug')
                                
                                active_threads[runner.ident] = runner
                                logger.log(f"Started new agent runner for team {team_name} (total: {len(active_threads)})")

                            except Exception as runner_error:
                                logger.log(f"Error creating/starting runner: {str(runner_error)}", 'error')
                                logger.log(traceback.format_exc(), 'debug')
                                continue

                        except Exception as config_error:
                            logger.log(f"Error creating agent config: {str(config_error)}", 'error')
                            logger.log(traceback.format_exc(), 'debug')
                            continue

                    except RuntimeError as e:
                        if "already exists" in str(e):
                            logger.log(str(e), 'debug')
                            continue
                        raise
                    except Exception as e:
                        logger.log(f"Error in agent creation loop: {str(e)}", 'error')
                        logger.log(traceback.format_exc(), 'debug')
                        continue

                    time.sleep(0.1)  # Brief pause between agent creation attempts

                # Process output queue
                try:
                    while True:  # Process all available messages
                        try:
                            msg = output_queue.get_nowait()
                            logger.log(f"Queue message - Status: {msg['status']}, Error: {msg.get('error', 'None')}", 'warning')
                        except queue.Empty:
                            break
                except Exception as queue_error:
                    logger.log(f"Error processing queue: {str(queue_error)}", 'error')

                time.sleep(1)  # Main loop sleep

            except Exception as e:
                logger.log(f"Error in main loop: {str(e)}", 'error')
                logger.log(traceback.format_exc(), 'debug')
                time.sleep(1)

    except KeyboardInterrupt:
        logger.log("Stopping multi-team execution...")
        
        # Stop all threads
        for runner in active_threads.values():
            runner.running = False
            
        # Wait for threads to finish
        for runner in active_threads.values():
            runner.join(timeout=1.0)

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='KinOS CLI')
    parser.add_argument('command', help='Command to execute')
    parser.add_argument('--name', help='Specific agent or team name for file context')
    parser.add_argument('--model', help='Model to use (e.g. "claude-3-haiku", "gpt-4", etc.)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    # Configuration du logger
    logger = Logger()
    if args.verbose:
        logger.set_level('debug')

    # New run command for multi-team execution
    if args.command == "run":
        # Validate model if provided
        if args.model:
            run_multi_team_loop(args.model)
        else:
            run_multi_team_loop()
        return

    # Existing team command logic
    if not args.name:
        logger.log("Error: --name is required", 'error')
        sys.exit(1)

    # Initialiser la structure de l'équipe
    initialize_team_structure(args.command, args.name)

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
        run_team_loop(team_name, args.name)

if __name__ == "__main__":
    main()
