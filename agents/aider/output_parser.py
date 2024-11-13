"""
AiderOutputParser - Parses and processes Aider command output
"""
import subprocess
from typing import Optional, Dict, Any, List
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
        
    def _parse_commit_message(self, line: str, output_lines: list) -> None:
        """
        Parse and format a commit message line
        
        Args:
            line: Line containing commit message
            output_lines: List to append formatted message to
        """
        try:
            # Extract commit hash and message
            parts = line.split()
            if len(parts) < 3:  # Need at least "Commit <hash> <message>"
                return
                
            commit_hash = parts[1]
            message = ' '.join(parts[2:])
            
            # Detect commit type
            commit_type = None
            for known_type in self.COMMIT_ICONS:
                if message.lower().startswith(f"{known_type}:"):
                    commit_type = known_type
                    message = message[len(known_type)+1:].strip()
                    break
                    
            # Get icon and format message
            icon = self.COMMIT_ICONS.get(commit_type, '🔨')
            formatted = f"{icon} {commit_hash}: {message}"
            
            output_lines.append(formatted)
            self.logger.log(formatted, 'info')
            
        except Exception as e:
            self.logger.log(f"Error parsing commit message: {str(e)}", 'error')

    def _parse_file_changes(self, output: str) -> Dict[str, Any]:
        """
        Parse file changes from output
        
        Args:
            output: Command output string
            
        Returns:
            Dict with changes info
        """
        changes = {
            'modified_files': set(),
            'added_files': set(),
            'deleted_files': set()
        }
        
        try:
            for line in output.splitlines():
                if "Wrote " in line:
                    file_path = line.split("Wrote ")[1].split()[0]
                    changes['modified_files'].add(file_path)
                elif "Created " in line:
                    file_path = line.split("Created ")[1].split()[0]
                    changes['added_files'].add(file_path)
                elif "Deleted " in line:
                    file_path = line.split("Deleted ")[1].split()[0]
                    changes['deleted_files'].add(file_path)
                    
            return changes
            
        except Exception as e:
            self.logger.log(f"Error parsing file changes: {str(e)}", 'error')
            return changes

    def _parse_error_messages(self, output: str) -> List[str]:
        """
        Extract error messages from output
        
        Args:
            output: Command output string
            
        Returns:
            List of error messages
        """
        errors = []
        
        try:
            for line in output.splitlines():
                lower_line = line.lower()
                if any(err in lower_line for err in [
                    'error', 'exception', 'failed', 'can\'t initialize'
                ]):
                    errors.append(line.strip())
                    
            return errors
            
        except Exception as e:
            self.logger.log(f"Error parsing errors: {str(e)}", 'error')
            return errors

    def _format_commit_message(self, commit_type: str, message: str) -> str:
        """
        Format commit message with icon
        
        Args:
            commit_type: Type of commit
            message: Commit message
            
        Returns:
            Formatted message with icon
        """
        icon = self.COMMIT_ICONS.get(commit_type, '🔨')
        return f"{icon} {message}"

    def _is_error_message(self, line: str) -> bool:
        """
        Check if line contains error message
        
        Args:
            line: Output line to check
            
        Returns:
            bool: True if line contains error
        """
        # Ignorer les erreurs connues d'Aider sur Windows
        known_aider_errors = [
            "Can't initialize prompt toolkit",
            "No Windows console found",
            "aider.chat/docs/troubleshooting/edit-errors.html"
        ]
        if any(err in line for err in known_aider_errors):
            return False
            
        # Documentation links should not be treated as errors
        if "documentation:" in line.lower():
            return False
            
        error_indicators = [
            'error',
            'exception', 
            'failed',
            'fatal:',
            'permission denied'
        ]
        return any(indicator in line.lower() for indicator in error_indicators)

    def _handle_error_message(self, line: str) -> None:
        """
        Handle error message in output
        
        Args:
            line: Output line containing error
        """
        # Log error message
        self.logger.log(
            f"Error detected in Aider output: {line.strip()}", 
            'error'
        )

    def _parse_file_modification(self, line: str, changes: Dict[str, set]) -> None:
        """
        Parse file modification line and update changes tracking
        
        Args:
            line: Output line containing file modification
            changes: Dictionary tracking file changes
        """
        try:
            if "Wrote " in line:
                file_path = line.split("Wrote ")[1].split()[0]
                changes['modified_files'].add(file_path)
                self.logger.log(f"✍️ Modified: {file_path}", 'info')
            elif "Created " in line:
                file_path = line.split("Created ")[1].split()[0]
                changes['added_files'].add(file_path)
                self.logger.log(f"➕ Created: {file_path}", 'info')
            elif "Deleted " in line:
                file_path = line.split("Deleted ")[1].split()[0]
                changes['deleted_files'].add(file_path)
                self.logger.log(f"➖ Deleted: {file_path}", 'info')
                
        except Exception as e:
            self.logger.log(f"Error parsing file modification: {str(e)}", 'error')

    def parse_output(self, process: subprocess.Popen) -> Optional[str]:
        """
        Parse Aider command output with enhanced error handling
        
        Args:
            process: Running Aider process
            
        Returns:
            Optional[str]: Parsed output or None on error
        """
        output_lines = []
        changes = {
            'modified_files': set(),
            'added_files': set(),
            'deleted_files': set()
        }
        has_results = False  # Flag pour suivre si on a des résultats
        
        try:
            # Collect all output with Windows error handling
            full_output = []
            current_commit = None
            
            while True:
                try:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    
                    line = line.rstrip()
                    if not line:
                        continue
                        
                    # Si c'est une nouvelle ligne de commit, sauvegarder la ligne complète
                    if line.startswith("Commit "):
                        current_commit = line
                        full_output.append(line)
                    # Si on a un commit en cours et que la ligne suivante n'est pas une nouvelle commande
                    elif current_commit and not any(cmd in line for cmd in ["Wrote ", "Created ", "Deleted ", "Running ", "$ git"]):
                        # Ajouter au message de commit précédent
                        current_commit += " " + line
                        # Mettre à jour la dernière ligne
                        full_output[-1] = current_commit
                    else:
                        current_commit = None
                        full_output.append(line)
                    
                    # Parse different line types
                    if "Wrote " in line:
                        self._parse_file_modification(line, changes)
                        has_results = True
                    elif line.startswith("Commit "):
                        if self._parse_commit_line(current_commit or line):
                            has_results = True
                    elif self._is_error_message(line):
                        self._handle_error_message(line)
                    else:
                        output_lines.append(line)
                        
                except OSError as os_error:
                    # Gérer l'erreur de flux Windows
                    if "[Errno 22] Invalid argument" in str(os_error):
                        # Essayer de récupérer le reste de la sortie
                        try:
                            remaining_output, _ = process.communicate()
                            if remaining_output:
                                if isinstance(remaining_output, bytes):
                                    remaining_output = remaining_output.decode('utf-8')
                                full_output.extend(remaining_output.splitlines())
                        except Exception:
                            pass
                        break
                    else:
                        raise

            # Get return code
            return_code = process.wait(timeout=5)
            
            # Combine output
            output = "\n".join(full_output)
            
            # Parse changes and errors
            changes = self._parse_file_changes(output)
            errors = self._parse_error_messages(output)
            
            if errors:
                self.logger.log(f"Errors detected:\n" + "\n".join(errors), 'error')
                return None
                
            if return_code != 0:
                self.logger.log(f"Process failed with code {return_code}", 'error')
                return None
                
            # Ne retourner None que si on n'a vraiment aucun résultat
            if not has_results:
                self.logger.log("⚠️ Aucun résultat de run_aider", 'warning')
                return None
                
            return output
            
        except Exception as e:
            self.logger.log(f"Error parsing output: {str(e)}", 'error')
            return None
            
    def _parse_commit_line(self, line: str) -> bool:
        """Parse and log a commit line"""
        try:
            # Vérifier que c'est bien une ligne de commit
            if not line or not line.startswith("Commit "):
                return False
                
            # Extraire le hash et le message complet
            # Utiliser split avec maxsplit=2 pour garder le reste du message intact
            parts = line.split(maxsplit=2)
            if len(parts) < 3:
                return False
                
            commit_hash = parts[1]
            full_message = parts[2]
            
            # Detect commit type from message
            commit_type = None
            message = full_message
            
            for known_type in self.COMMIT_ICONS:
                prefix = f"{known_type}:"
                if full_message.lower().startswith(prefix.lower()):
                    commit_type = known_type
                    message = full_message[len(prefix):].strip()
                    break
                    
            # Get icon and log with proper formatting
            icon = self.COMMIT_ICONS.get(commit_type, '🔨')
            
            # Log avec un niveau 'success' pour être sûr qu'il s'affiche
            self.logger.log(
                f"{icon} {commit_hash}: {message}",
                'success'
            )
            
            # Indiquer qu'on a bien eu un résultat
            return True
            
        except Exception as e:
            self.logger.log(f"Error parsing commit: {str(e)}", 'error')
            return False
