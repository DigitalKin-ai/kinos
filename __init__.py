"""
KinOS - Autonomous Agent Framework
"""
import os
import logging
from typing import Dict, Any, Optional

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Core imports
from config.global_config import GlobalConfig
from utils.path_manager import PathManager
from utils.logger import Logger
from utils.model_router import ModelRouter

# Agent imports
from agents.aider.aider_agent import AiderAgent
from agents.research.research_agent import ResearchAgent
from agents.base.agent_base import AgentBase

# Service imports 
from services.team_service import TeamService
from services.agent_service import AgentService
from services.map_service import MapService

# Initialize logger
logger = Logger()

def init_kinos(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Initialize KinOS framework
    
    Args:
        config: Optional configuration override
        
    Returns:
        bool: True if initialization successful
    """
    try:
        # Ensure required directories
        GlobalConfig.ensure_directories()
        
        # Initialize services
        from services import init_services
        services = init_services(config)
        
        logger.log("KinOS initialized successfully", 'info')
        return True
        
    except Exception as e:
        logger.log(f"Error initializing KinOS: {str(e)}", 'error')
        return False

# Export public interface
__all__ = [
    # Core classes
    'AiderAgent',
    'ResearchAgent',
    'AgentBase',
    
    # Services
    'TeamService',
    'AgentService',
    'MapService',
    
    # Utilities
    'Logger',
    'ModelRouter',
    'PathManager',
    
    # Functions
    'init_kinos'
]
