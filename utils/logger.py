import os
import logging
from colorama import init, Fore, Style
import openai
from dotenv import load_dotenv

class Logger:
    """Utility class for handling logging operations."""
    
    # Class variable for global log level
    _global_level = logging.SUCCESS
    
    def __init__(self):
        """Initialize the logger with mission context."""
        # Force UTF-8 for stdin/stdout
        import sys
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')

        # Load mission context
        self.mission_content = self._load_mission_content()
        
        # Set locale to UTF-8
        import locale
        try:
            locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
        except locale.Error:
            pass  # Continue if locale not available
            
        # Initialize colorama for cross-platform color support
        init()
        
        # Add SUCCESS level between INFO and WARNING
        logging.SUCCESS = 25  # Between INFO(20) and WARNING(30)
        logging.addLevelName(logging.SUCCESS, 'SUCCESS')

        # Initialize OpenAI
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
            
        # Initialize suivi file path and handler
        self.suivi_file = 'suivi.md'
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                         datefmt='%Y-%m-%d %H:%M:%S')

        # Initialize file handler with UTF-8 encoding
        file_handler = logging.FileHandler(self.suivi_file, encoding='utf-8', mode='a')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.SUCCESS)  # Only log SUCCESS and above

        # Custom formatter with colors for console
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

        # Setup console handler with color formatter and SUCCESS level by default
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.SUCCESS)  # Set default handler level to SUCCESS
        console_handler.setFormatter(ColorFormatter())
        
        # Configure logger with global level
        self.logger = logging.getLogger('KinOS')
        self.logger.setLevel(self._global_level)
        
        # Remove existing handlers and add our handlers
        self.logger.handlers = []
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        # Set handler levels to match global level
        for handler in self.logger.handlers:
            handler.setLevel(self._global_level)
        
        # Prevent propagation to root logger
        self.logger.propagate = False

    @classmethod
    def set_global_level(cls, level):
        """Set the global logging level for all logger instances."""
        cls._global_level = level
        # Update existing loggers
        for logger in logging.Logger.manager.loggerDict.values():
            if isinstance(logger, logging.Logger):
                logger.setLevel(level)
                for handler in logger.handlers:
                    handler.setLevel(level)
        
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
        self._check_and_summarize_logs()  # Check size after adding new log
        
    def warning(self, message):
        """Log warning level message in yellow with agent emoji if present."""
        formatted_msg = self._get_agent_emoji(message)
        self.logger.warning(formatted_msg)
        
    def fix_file_encoding(self, filepath):
        """Convert file to UTF-8 if needed."""
        try:
            # Try reading with UTF-8 first
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                return  # File is already UTF-8
        except UnicodeDecodeError:
            self.logger.warning(f"⚠️ File {filepath} needs UTF-8 conversion")
            # Ask for confirmation
            if input(f"Convert {filepath} to UTF-8? (y/n) ").lower() != 'y':
                return
                
            # Try to detect encoding
            import chardet
            with open(filepath, 'rb') as f:
                raw = f.read()
            detected = chardet.detect(raw)
            encoding = detected['encoding']
            
            if encoding and encoding != 'utf-8':
                # Convert to UTF-8
                content = raw.decode(encoding)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.logger.success(f"✅ Converted {filepath} from {encoding} to UTF-8")
        
    def _load_mission_content(self):
        """Load mission content from .aider.mission.md file."""
        try:
            if os.path.exists('.aider.mission.md'):
                with open('.aider.mission.md', 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            print(f"Warning: Could not load mission file: {str(e)}")
            return ""

    def _check_and_summarize_logs(self):
        """Check log file size and summarize if needed with mission context."""
        try:
            if not os.path.exists(self.suivi_file):
                return

            # First close the current handler
            for handler in self.logger.handlers[:]:
                if isinstance(handler, logging.FileHandler) and handler.baseFilename == os.path.abspath(self.suivi_file):
                    handler.close()
                    self.logger.removeHandler(handler)
            
            # Try different encodings to read the file
            content = None
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(self.suivi_file, 'r', encoding=encoding) as f:
                        content = f.read()
                    self.logger.debug(f"Successfully read file with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
                    
            if content is None:
                raise ValueError(f"Could not read {self.suivi_file} with any supported encoding")
                
            if len(content) > 25000:
                # Format multi-line commit messages with proper indentation
                formatted_lines = []
                current_entry = []
                
                for line in content.split('\n'):
                    if line.startswith('20'):  # New timestamp entry
                        # Print previous entry if exists
                        if current_entry:
                            formatted_lines.extend(current_entry)
                            formatted_lines.append('')  # Add blank line between entries
                            current_entry = []
                        current_entry.append(line)
                    elif line.strip():  # Content line (part of commit message)
                        # Indent continuation lines
                        current_entry.append('    ' + line.strip())
                    else:  # Empty line
                        if current_entry:
                            formatted_lines.extend(current_entry)
                            formatted_lines.append('')  # Add blank line between entries
                            current_entry = []
                        formatted_lines.append('')  # Preserve empty lines

                # Add any remaining entry
                if current_entry:
                    formatted_lines.extend(current_entry)
                    formatted_lines.append('')

                # Join all lines with newlines
                formatted_content = '\n'.join(formatted_lines)

                # Continue with GPT summarization...
                self.logger.log(logging.SUCCESS, "📝 Generating mission tracking...")
                
                client = openai.OpenAI()
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": """You are an expert project progress analyst.
Your task is to summarize project logs in relation to the mission objectives.

Focus on:
1. Progress towards mission goals
2. Key decisions and their alignment with objectives
3. Problems encountered and solutions found
4. Critical file modifications and their purpose
5. Team coordination and agent interactions

Format your summary in markdown with clear sections:
- Mission Progress
- Key Achievements
- Technical Changes
- Coordination Notes
- Next Steps"""},
                        {"role": "user", "content": f"""# Project Mission
````
{self.mission_content}
````

# Recent Logs to Summarize
````
{formatted_content}
````

# Instructions
Create a detailed progress summary that shows how recent activities align with mission objectives."""}
                    ],
                    temperature=0.3,
                    max_tokens=4000
                )
                
                summary = response.choices[0].message.content
                
                # Add header to summary
                final_content = "# Résumé des logs précédents\n\n"
                final_content += summary
                final_content += "\n\n# Nouveaux logs\n\n"
                
                # Write new summary with utf-8 encoding
                with open(self.suivi_file, 'w', encoding='utf-8') as f:
                    f.write(final_content)
                    
                self.logger.log(logging.SUCCESS, "✨ Mission tracking summarized successfully")
            
            # Re-add the file handler
            file_handler = logging.FileHandler(self.suivi_file, encoding='utf-8', mode='a')
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                             datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(logging.SUCCESS)
            self.logger.addHandler(file_handler)
                
        except Exception as e:
            self.logger.error(f"⚠️ Error summarizing mission tracking: {str(e)}")
            # Make sure we restore the file handler even if there's an error
            file_handler = logging.FileHandler(self.suivi_file, encoding='utf-8', mode='a')
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                             datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(logging.SUCCESS)
            self.logger.addHandler(file_handler)
