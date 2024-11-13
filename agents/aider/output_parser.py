"""
AiderOutputParser - Parses and processes Aider command output
"""
import subprocess
from typing import Optional, Dict, Any
from utils.logger import Logger

class AiderOutputParser:
    """Parses Aider command output"""
    
    # Commit type icons
    COMMIT_ICONS = {
        'feat': '✨',     # New feature
        'fix': '🐛',      # Bug fix
        'docs': '📚',     # Documentation
        'style': '💎',    # Style/formatting
        'refactor': '♻️',  # Refactoring
        'perf': '⚡️',     # Performance
        'test': '🧪',     # Tests
        'build': '📦',    # Build/dependencies
        'ci': '🔄',       # CI/CD
        'chore': '🔧',    # Maintenance
        'revert': '⏪',    # Revert changes
        'merge': '🔗',    # Merge changes
        'update': '📝',   # Content updates
        'add': '➕',      # Add content/files
        'remove': '➖',    # Remove content/files
        'move': '🚚',     # Move/rename content
        'cleanup': '🧹',  # Code cleanup
        'format': '🎨',   # Formatting changes
        'optimize': '🚀'  # Optimizations
    }
    
    def __init__(self, logger: Logger):
        """Initialize with logger"""
        self.logger = logger
        
    def parse_output(self, process: subprocess.Popen) -> Optional[str]:
        """
        Parse Aider command output
        
        Args:
            process: Running Aider process
            
        Returns:
            Optional[str]: Parsed output or None on error
        """
        output_lines = []
        error_detected = False
        
        try:
            # Read output while process is running
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                    
                line = line.rstrip()
                if not line:
                    continue
                    
                # Handle Windows console warning
                if "No Windows console found" in line:
                    self.logger.log(
                        "Windows console initialization warning - non-critical",
                        'warning'
                    )
                    continue
                    
                # Parse commit messages
                if "Commit" in line:
                    self._parse_commit_line(line)
                else:
                    # Check for errors
                    lower_line = line.lower()
                    is_error = any(err in lower_line for err in [
                        'error', 'exception', 'failed', 'can\'t initialize'
                    ])
                    
                    if is_error:
                        self.logger.log(f"Error detected: {line}", 'error')
                        error_detected = True
                    else:
                        self.logger.log(line, 'info')
                        
                output_lines.append(line)
                
            # Get return code
            return_code = process.wait(timeout=5)
            
            # Check for success
            if return_code != 0 or error_detected:
                self.logger.log(
                    f"Aider failed (code: {return_code})",
                    'error'
                )
                return None
                
            # Combine output
            return "\n".join(output_lines)
            
        except Exception as e:
            self.logger.log(f"Error parsing output: {str(e)}", 'error')
            return None
            
    def _parse_commit_line(self, line: str) -> None:
        """Parse and log a commit line"""
        try:
            # Extract commit hash and message
            parts = line.split()
            commit_hash = parts[1]
            message = ' '.join(parts[2:])
            
            # Detect commit type
            commit_type = None
            for known_type in self.COMMIT_ICONS:
                if message.lower().startswith(f"{known_type}:"):
                    commit_type = known_type
                    message = message[len(known_type)+1:].strip()
                    break
                    
            # Get icon
            icon = self.COMMIT_ICONS.get(commit_type, '🔨')
            
            # Log commit
            self.logger.log(
                f"{icon} {commit_hash}: {message}",
                'success'
            )
            
        except Exception as e:
            self.logger.log(f"Error parsing commit: {str(e)}", 'error')
