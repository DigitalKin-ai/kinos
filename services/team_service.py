"""Team configuration and management service"""
import os
import json
from typing import Dict, Any, List, Optional, Tuple
import os
import json
from services.base_service import BaseService
from utils.exceptions import ServiceError
from utils.path_manager import PathManager

class TeamService(BaseService):
    """Manages team configurations and state"""

    def __init__(self, _):  # Keep parameter for compatibility but don't use it
        """Initialize with minimal dependencies"""
        super().__init__(_)
        self.active_team = None
        self.team_types = self._load_team_types()

    def _load_team_types(self) -> List[Dict[str, Any]]:
        """Load team configurations from local team directories"""
        try:
            teams = []
            current_dir = os.getcwd()
            
            # Look for team_* directories in current directory
            for item in os.listdir(current_dir):
                if not item.startswith('team_'):
                    continue
                    
                team_dir = os.path.join(current_dir, item)
                if not os.path.isdir(team_dir):
                    continue

                # Load config from team directory
                config_path = os.path.join(team_dir, "config.json")
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            
                        # Set ID from directory name if not present
                        if 'id' not in config:
                            config['id'] = item.replace('team_', '')
                            
                        # Normalize agent configurations
                        if 'agents' in config:
                            config['agents'] = [
                                {
                                    'name': agent if isinstance(agent, str) else agent.get('name', 'unnamed'),
                                    'type': 'aider' if isinstance(agent, str) else agent.get('type', 'aider'),
                                    'weight': 0.5 if isinstance(agent, str) else agent.get('weight', 0.5)
                                }
                                for agent in config['agents']
                            ]
                            
                        # Validate configuration
                        valid, error = self.validate_team_config(config)
                        if valid:
                            teams.append(config)
                        else:
                            self.logger.log(f"Invalid team config {item}: {error}", 'warning')
                            
                    except Exception as e:
                        self.logger.log(f"Error loading team {item}: {str(e)}", 'error')
            
            return teams

        except Exception as e:
            self.logger.log(f"Error loading teams: {str(e)}", 'error')
            return []

    def _generate_default_config(self, name: str) -> Dict[str, Any]:
        """
        Generate default team configuration
        
        Args:
            name: Team name
            
        Returns:
            Dict with default team configuration
        """
        try:
            # Generate display name from team name
            display_name = name.replace('_', ' ').title()
            
            # Default agent configuration
            default_agents = [
                {
                    "name": "specifications",
                    "type": "aider",
                    "weight": 0.4
                },
                {
                    "name": "management",
                    "type": "aider", 
                    "weight": 0.6
                },
                {
                    "name": "evaluation",
                    "type": "aider",
                    "weight": 0.3
                },
                {
                    "name": "redacteur",
                    "type": "aider",
                    "weight": 1.0
                },
                {
                    "name": "documentaliste",
                    "type": "research",
                    "weight": 0.2
                }
            ]
            
            # Create config structure
            config = {
                "name": name,
                "display_name": display_name,
                "description": f"Auto-generated team configuration for {display_name}",
                "agents": default_agents
            }
            
            # Save config file in team directory
            team_dir = os.path.join(os.getcwd(), f"team_{team_id}")
            os.makedirs(team_dir, exist_ok=True)
            
            config_path = os.path.join(team_dir, "config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
                
            self.logger.log(f"Generated new config file for team {team_id}", 'info')
            return config
            
        except Exception as e:
            self.logger.log(f"Error generating config for team {team_id}: {str(e)}", 'error')
            return None

    def get_team_config(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific team with config generation
    
        Args:
            name: Team name
    
        Returns:
            Team configuration dictionary or None if not found
        """
        try:
            # First, try to find the team's specific config
            team_dir = os.path.join(os.getcwd(), f"team_{name}")
            config_path = os.path.join(team_dir, "config.json")
        
            # If no specific team config exists, generate one
            if not os.path.exists(config_path):
                return self._generate_default_config(name)
        
            # Load the specific team config
            with open(config_path, 'r', encoding='utf-8') as f:
                team_config = json.load(f)
        
            return team_config
        
        except Exception as e:
            self.logger.log(f"Error getting team config for {name}: {str(e)}", 'error')
            return None

    def set_active_team(self, name: str) -> bool:
        """Set the active team configuration"""
        try:
            # Normalize team name by removing 'team_' prefix if present
            normalized_name = name.replace('team_', '')
            
            # Get team config
            team_config = self.get_team_config(normalized_name)
            if not team_config:
                # Try to generate default config if none exists
                team_config = self._generate_default_config(normalized_name)
                if not team_config:
                    raise ServiceError(f"Team not found and couldn't create default: {normalized_name}")
            
            # Store active team
            self.active_team = team_config
            
            # Create team directory if it doesn't exist
            team_dir = os.path.join(os.getcwd(), f"team_{normalized_name}")
            os.makedirs(team_dir, exist_ok=True)
            
            # Create history directory for team
            history_dir = os.path.join(team_dir, "history")
            os.makedirs(history_dir, exist_ok=True)
            
            # Create subdirectories if needed
            for subdir in ['chat', 'input', 'output', 'agents']:
                os.makedirs(os.path.join(history_dir, subdir), exist_ok=True)
            
            self.logger.log(f"Active team set to: {normalized_name} ({team_config.get('display_name', normalized_name)})", 'success')
            return True
            
        except Exception as e:
            self.logger.log(f"Error setting active team: {str(e)}", 'error')
            return False

    def get_active_team(self) -> Optional[Dict[str, Any]]:
        """Get the currently active team configuration"""
        try:
            # If no active team, try to find team from current directory
            if not self.active_team:
                current_dir = os.getcwd()
                team_dirs = [d for d in os.listdir(current_dir) if d.startswith('team_')]
                
                for team_dir in team_dirs:
                    team_id = team_dir.replace('team_', '')
                    team_config = self.get_team_config(team_id)
                    if team_config:
                        self.active_team = team_config
                        break
                
                # If still no active team, use default
                if not self.active_team:
                    self.set_active_team('default')
            
            return self.active_team
            
        except Exception as e:
            self.logger.log(f"Error getting active team: {str(e)}", 'error')
            return None

    def get_team_agents(self, team_id: Optional[str] = None) -> List[str]:
        """Get list of agent names for a team"""
        try:
            # Use active team if no ID provided
            config = self.get_team_config(team_id) if team_id else self.active_team
        
            if not config:
                self.logger.log(f"No configuration found for team: {team_id}", 'warning')
                return []
        
            # Extract agent names
            agents = []
            for agent in config.get('agents', []):
                if isinstance(agent, dict):
                    agents.append(agent.get('name', ''))
                elif isinstance(agent, str):
                    agents.append(agent)
        
            # Remove any empty agent names
            agents = [a for a in agents if a]
        
            if not agents:
                self.logger.log(f"No agents found in team configuration for: {team_id}", 'warning')
        
            return agents
        
        except Exception as e:
            self.logger.log(f"Error getting team agents: {str(e)}", 'error')
            return []

    def validate_team_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate team configuration format"""
        try:
            # Check required fields
            required = ['id', 'name', 'agents']
            missing = [f for f in required if f not in config]
            if missing:
                return False, f"Missing required fields: {', '.join(missing)}"
                
            # Validate agents
            if not config['agents']:
                return False, "No agents defined"
                
            for agent in config['agents']:
                if isinstance(agent, dict):
                    if 'name' not in agent:
                        return False, f"Missing name in agent config: {agent}"
                elif not isinstance(agent, str):
                    return False, f"Invalid agent format: {agent}"
                    
            return True, None
            
        except Exception as e:
            return False, str(e)

    def load_team_prompts(self, team_id: str) -> Dict[str, str]:
        """Load all prompt files for a team"""
        try:
            prompts = {}
            team_dir = os.path.join(PathManager.get_teams_root(), team_id)
            
            if not os.path.exists(team_dir):
                self.logger.log(f"Team directory not found: {team_id}", 'warning')
                return prompts
                
            # Load each .md file as a prompt
            for file in os.listdir(team_dir):
                if file.endswith('.md'):
                    prompt_path = os.path.join(team_dir, file)
                    try:
                        with open(prompt_path, 'r', encoding='utf-8') as f:
                            agent_name = file[:-3]  # Remove .md extension
                            prompts[agent_name] = f.read()
                    except Exception as e:
                        self.logger.log(f"Error loading prompt {file}: {str(e)}", 'warning')
                        
            return prompts
            
        except Exception as e:
            self.logger.log(f"Error loading team prompts: {str(e)}", 'error')
            return {}

    def validate_team_prompts(self, team_id: str) -> Dict[str, List[str]]:
        """Validate all prompts for a team"""
        validation_results = {
            'valid': [],
            'invalid': [],
            'missing': []
        }
        
        try:
            team_config = self.get_team_config(team_id)
            if not team_config:
                return validation_results
                
            # Get expected agents
            expected_agents = self.get_team_agents(team_id)
            
            # Load and validate each prompt
            prompts = self.load_team_prompts(team_id)
            
            for agent in expected_agents:
                if agent not in prompts:
                    validation_results['missing'].append(agent)
                    continue
                    
                # Basic validation - check for required sections
                prompt_content = prompts[agent]
                required_sections = ['MISSION:', 'CONTEXT:', 'INSTRUCTIONS:', 'RULES:']
                
                if all(section in prompt_content for section in required_sections):
                    validation_results['valid'].append(agent)
                else:
                    validation_results['invalid'].append(agent)
                    
            return validation_results
            
        except Exception as e:
            self.logger.log(f"Error validating team prompts: {str(e)}", 'error')
            return validation_results

    def get_agent_prompt_path(self, team_id: str, agent_name: str) -> Optional[str]:
        """Get prompt file path for an agent in a team"""
        try:
            team_dir = os.path.join(PathManager.get_kinos_root(), "teams", team_id)
            prompt_file = os.path.join(team_dir, f"{agent_name.lower()}.md")
            
            if os.path.exists(prompt_file):
                return prompt_file
            return None
            
        except Exception as e:
            self.logger.log(f"Error getting agent prompt path: {str(e)}", 'error')
            return None

    def get_agent_prompt_path(self, team_id: str, agent_name: str) -> Optional[str]:
        """Get prompt file path for an agent in a team"""
        try:
            team_dir = os.path.join(PathManager.get_kinos_root(), "teams", team_id)
            prompt_file = os.path.join(team_dir, f"{agent_name.lower()}.md")
            
            if os.path.exists(prompt_file):
                return prompt_file
            return None
            
        except Exception as e:
            self.logger.log(f"Error getting agent prompt path: {str(e)}", 'error')
            return None

    def cleanup(self):
        """Cleanup team service resources"""
        try:
            self.active_team = None
            self.team_types.clear()
        except Exception as e:
            self.logger.log(f"Error cleaning up team service: {str(e)}", 'error')
