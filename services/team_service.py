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
        self.active_team_name = None  # Add explicit team name tracking
        self.team_types = self._load_team_types()

    def _load_team_types(self) -> List[Dict[str, Any]]:
        """Load team configurations from local team directories"""
        try:
            teams = []
            current_dir = os.getcwd()
            
            # Scan for team directories
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
                            self.logger.log(f"Loaded team configuration: {config['name']}", 'info')
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
            team_dir = os.path.join(os.getcwd(), f"team_{name}")
            os.makedirs(team_dir, exist_ok=True)
            
            config_path = os.path.join(team_dir, "config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
                
            self.logger.log(f"Generated new config file for team {name}", 'info')
            return config
            
        except Exception as e:
            self.logger.log(f"Error generating config for team {name}: {str(e)}", 'error')
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

    def set_active_team(self, name: str, force: bool = False) -> bool:
        """
        Set the active team configuration
        
        Args:
            name: Team name to set
            force: Force team switch even if already active
        """
        try:
            # Normalize team name
            normalized_name = name.replace('team_', '')
            
            # Don't change team if already set to this team unless forced
            if not force and self.active_team_name == normalized_name:
                self.logger.log(f"Team {normalized_name} already active", 'debug')
                return True
                
            # Get team config
            team_config = self.get_team_by_name(normalized_name)
            if not team_config:
                raise ServiceError(f"Team '{normalized_name}' not found - Please create team directory and config first")
            
            # Store active team and name
            self.active_team = team_config
            self.active_team_name = normalized_name
            
            # Create team directory structure
            team_dir = os.path.join(os.getcwd(), f"team_{name}")
            os.makedirs(team_dir, exist_ok=True)
            
            for subdir in ['history', 'prompts', 'data']:
                os.makedirs(os.path.join(team_dir, subdir), exist_ok=True)
            
            self.logger.log(f"Active team set to: {name} ({team_config.get('display_name', name)})", 'success')
            return True
            
        except Exception as e:
            self.logger.log(f"Error setting active team: {str(e)}", 'error')
            raise ServiceError(f"Failed to set team '{name}': {str(e)}")

    def get_active_team(self) -> Optional[Dict[str, Any]]:
        """Get the currently active team configuration"""
        if not self.active_team:
            raise ServiceError("No active team set")
        return self.active_team

    def get_team_agents(self, team_name: Optional[str] = None) -> List[str]:
        """Get list of agent names for a team"""
        try:
            # Use active team if no name provided
            if team_name:
                config = self.get_team_by_name(team_name)
            else:
                config = self.active_team
        
            if not config:
                self.logger.log(f"No configuration found for team: {team_name}", 'warning')
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
                self.logger.log(f"No agents found in team configuration for: {team_name}", 'warning')
        
            return agents
        
        except Exception as e:
            self.logger.log(f"Error getting team agents: {str(e)}", 'error')
            return []

    def validate_team_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate team configuration format"""
        try:
            # Check required fields - display_name is optional
            required = ['name', 'agents']
            missing = [f for f in required if f not in config]
            if missing:
                return False, f"Missing required fields: {', '.join(missing)}"
            
            # Set display_name to name if not provided
            if 'display_name' not in config:
                config['display_name'] = config['name']
                
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

    def load_team_prompts(self, team_name: str) -> Dict[str, str]:
        """Load all prompt files for a team"""
        try:
            prompts = {}
            team_dir = os.path.join(PathManager.get_teams_root(), team_name)
            
            if not os.path.exists(team_dir):
                self.logger.log(f"Team directory not found: {team_name}", 'warning')
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

    def validate_team_prompts(self, team_name: str) -> Dict[str, List[str]]:
        """Validate all prompts for a team"""
        validation_results = {
            'valid': [],
            'invalid': [],
            'missing': []
        }
        
        try:
            team_config = self.get_team_config(team_name)
            if not team_config:
                return validation_results
                
            # Get expected agents
            expected_agents = self.get_team_agents(team_name)
            
            # Load and validate each prompt
            prompts = self.load_team_prompts(team_name)
            
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

    def get_agent_prompt_path(self, team_name: str, agent_name: str) -> Optional[str]:
        """Get prompt file path for an agent in a team"""
        try:
            team_dir = os.path.join(PathManager.get_kinos_root(), "teams", team_name)
            prompt_file = os.path.join(team_dir, f"{agent_name.lower()}.md")
            
            if os.path.exists(prompt_file):
                return prompt_file
            return None
            
        except Exception as e:
            self.logger.log(f"Error getting agent prompt path: {str(e)}", 'error')
            return None

    def get_agent_prompt_path(self, team_name: str, agent_name: str) -> Optional[str]:
        """Get prompt file path for an agent in a team"""
        try:
            team_dir = os.path.join(PathManager.get_kinos_root(), "teams", team_name)
            prompt_file = os.path.join(team_dir, f"{agent_name.lower()}.md")
            
            if os.path.exists(prompt_file):
                return prompt_file
            return None
            
        except Exception as e:
            self.logger.log(f"Error getting agent prompt path: {str(e)}", 'error')
            return None

    def get_team_by_name(self, team_name: str) -> Optional[Dict[str, Any]]:
        """
        Get team configuration by name
        
        Args:
            team_name: Name of the team to find
            
        Returns:
            Optional[Dict[str, Any]]: Team configuration or None if not found
        """
        try:
            # Normalize team name by removing 'team_' prefix if present
            normalized_name = team_name.replace('team_', '')
            
            # First check if this is the active team
            if self.active_team and self.active_team.get('name') == normalized_name:
                return self.active_team
                
            # Look through team configurations
            for team in self.team_types:
                if team.get('name') == normalized_name:
                    return team
                    
            # If not found, try to load from filesystem
            team_dir = os.path.join(os.getcwd(), f"team_{normalized_name}")
            if os.path.exists(team_dir):
                config_path = os.path.join(team_dir, "config.json")
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        return config
                    except Exception as e:
                        raise ServiceError(f"Error loading team config: {str(e)}")
                    
            raise ServiceError(f"Team '{normalized_name}' not found")
            
        except Exception as e:
            self.logger.log(f"Error getting team by name: {str(e)}", 'error')
            raise ServiceError(f"Failed to get team '{team_name}': {str(e)}")

    def cleanup(self):
        """Cleanup team service resources"""
        try:
            self.active_team = None
            self.team_types.clear()
        except Exception as e:
            self.logger.log(f"Error cleaning up team service: {str(e)}", 'error')
