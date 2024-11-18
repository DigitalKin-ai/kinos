import logging
from colorama import init, Fore, Style

class Logger:
    """Utility class for handling logging operations."""
    
    def __init__(self):
        # Initialize colorama for cross-platform color support
        init()
        
        # Add SUCCESS level between INFO and WARNING
        logging.SUCCESS = 25  # Between INFO(20) and WARNING(30)
        logging.addLevelName(logging.SUCCESS, 'SUCCESS')
        
        # Add file handler for suivi.md
        self.suivi_file = 'suivi.md'
        file_formatter = logging.Formatter('%(asctime)s - %(message)s',
                                         datefmt='%Y-%m-%d %H:%M:%S')
        file_handler = logging.FileHandler(self.suivi_file, encoding='utf-8', mode='a')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.SUCCESS)  # Only log SUCCESS and above
        
        # Custom formatter with colors
        class ColorFormatter(logging.Formatter):
            FORMATS = {
                logging.DEBUG: Fore.CYAN + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
                logging.INFO: Fore.GREEN + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
                logging.SUCCESS: Fore.BLUE + Style.BRIGHT + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
                logging.WARNING: Fore.YELLOW + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
                logging.ERROR: Fore.RED + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL,
                logging.CRITICAL: Fore.RED + Style.BRIGHT + '%(asctime)s - %(levelname)s - %(message)s' + Style.RESET_ALL
            }

            def format(self, record):
                log_fmt = self.FORMATS.get(record.levelno)
                formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
                return formatter.format(record)

        # Setup handler with color formatter
        handler = logging.StreamHandler()
        handler.setFormatter(ColorFormatter())
        
        # Configure logger
        self.logger = logging.getLogger('KinOS')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers and add our handlers
        self.logger.handlers = []
        self.logger.addHandler(handler)
        self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
        
    def _get_agent_emoji(self, text):
        """Parse text for agent names and add their emoji prefixes."""
        # Map of agent types to emojis
        agent_emojis = {
            'specification': '📌',
            'management': '🧭', 
            'redaction': '🖋️',
            'evaluation': '⚖️',
            'deduplication': '👥',
            'chroniqueur': '📜',
            'redondance': '🎭',
            'production': '🏭',
            'chercheur': '🔬',
            'integration': '🌐'
        }
        
        # Replace agent names with emoji prefixed versions
        modified_text = text
        for agent_type, emoji in agent_emojis.items():
            # Look for agent name with various prefixes/formats
            patterns = [
                f"agent {agent_type}",
                f"Agent {agent_type}",
                f"l'agent {agent_type}",
                f"L'agent {agent_type}"
            ]
            
            for pattern in patterns:
                modified_text = modified_text.replace(
                    pattern, 
                    f"{pattern[:pattern.index(agent_type)]}{emoji} {agent_type}"
                )
                
        return modified_text

    def info(self, message):
        """Log info level message in green with agent emoji if present."""
        self.logger.info(self._get_agent_emoji(message))
        
    def error(self, message):
        """Log error level message in red with agent emoji if present."""
        formatted_msg = self._get_agent_emoji(message)
        self.logger.error(formatted_msg)
        
    def debug(self, message):
        """Log debug level message in cyan with agent emoji if present."""
        formatted_msg = self._get_agent_emoji(message)
        self.logger.debug(formatted_msg)
        
    def success(self, message):
        """Log success level message in bright blue with agent emoji if present."""
        formatted_msg = self._get_agent_emoji(message)
        self.logger.log(logging.SUCCESS, formatted_msg)
        
    def warning(self, message):
        """Log warning level message in yellow with agent emoji if present."""
        formatted_msg = self._get_agent_emoji(message)
        self.logger.warning(formatted_msg)
