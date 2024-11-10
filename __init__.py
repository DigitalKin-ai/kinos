# Root package initialization
# Root package initialization
# Import key modules or set package-level configurations

from config.global_config import GlobalConfig
from utils.path_manager import PathManager

# Optional: Set up logging or other global configurations
GlobalConfig.ensure_directories()
