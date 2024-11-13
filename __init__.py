"""KinOS initialization"""
from config.global_config import GlobalConfig
from utils.path_manager import PathManager
from agents.aider.aider_agent import AiderAgent
from agents.research.research_agent import ResearchAgent

# Initialize core components
GlobalConfig.ensure_directories()

# Export key classes
__all__ = ['AiderAgent', 'ResearchAgent']
