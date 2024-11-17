"""
AiderOutputParser - Parses and processes Aider command output
"""
import os
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
    
    def __init__(self, logger: Logger, agent_name: str):
        """Initialize with logger and agent name"""
        self.logger = logger
        self.agent_name = agent_name
        
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
                return True
                
            commit_hash = parts[1]
            message = ' '.join(parts[2:])
            
            # Get team ID from agent name using team service
            from services import init_services
            services = init_services(None)
            team_service = services['team_service']
            
            team_name = None
            for team in team_service.team_types:
                if self.agent_name in team_service.get_team_agents(team['id']):
                    team_name = team.get('name', team_name)
                    break
            
            # Detect commit type
            commit_type = None
            for known_type in self.COMMIT_ICONS:
                if message.lower().startswith(f"{known_type}:"):
                    commit_type = known_type
                    message = message[len(known_type)+1:].strip()
                    break
                    
            # Get icon and format message with team
            icon = self.COMMIT_ICONS.get(commit_type, '🔨')
            team_tag = f"[{team_name or 'no-team'}]" if team_name else "[no-team]"
            
            # Extract modified files from previous lines
            modified_files = []
            for prev_line in reversed(output_lines[-10:]):  # Look at last 10 lines
                if "Wrote " in prev_line:
                    file_path = prev_line.split("Wrote ")[1].split()[0]
                    modified_files.append(os.path.basename(file_path))
                elif "Created " in prev_line:
                    file_path = prev_line.split("Created ")[1].split()[0]
                    modified_files.append(os.path.basename(file_path))
                    
            # Add files to message if any were found
            files_info = f" ({', '.join(modified_files)})" if modified_files else ""
            
            # Format final message with team tag first and files info
            formatted = f"{team_tag} [{self.agent_name}] {icon} {commit_hash}: {message}{files_info}"
            
            output_lines.append(formatted)
            self.logger.log(formatted, 'info')
            
            # Never trigger shutdown regardless of commit message
            return True
            
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
        Extract and filter error messages from output
    
        Args:
            output: Command output string
        
        Returns:
            List of filtered error messages
        """
        errors = []
    
        try:
            for line in output.splitlines():
                lower_line = line.lower()
            
                # Ignore specific Aider-related non-critical errors
                ignore_patterns = [
                    'search/replace block failed to match',
                    'searchreplacenomatch',
                    'can\'t initialize prompt toolkit',
                    'no windows console found',
                    'aider.chat/docs/troubleshooting/edit-errors.html'
                ]
            
                if any(err in lower_line for err in ignore_patterns):
                    self.logger.log(f"Ignored non-critical error: {line}", 'debug')
                    continue
            
                error_indicators = [
                    'error', 
                    'exception', 
                    'failed',
                    'fatal:',
                    'permission denied'
                ]
            
                if any(indicator in lower_line for indicator in error_indicators):
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
        # Ignore known benign Aider errors
        known_errors = [
            "Can't initialize prompt toolkit",
            "No Windows console found",
            "aider.chat/docs/troubleshooting/edit-errors.html",
            "[Errno 22] Invalid argument"
        ]
        if any(err in line for err in known_errors):
            return False

        # Documentation links and version checks should not be treated as errors
        if "documentation:" in line.lower() or "Error checking pypi for new version" in line:
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

    def parse_output(self, process: subprocess.Popen) -> str:
        """
        Parse Aider command output with enhanced error handling
        
        Args:
            process: Running Aider process
            
        Returns:
            str: Parsed output, empty string on error to prevent shutdown
        """
        output_lines = []
        changes = {
            'modified_files': set(),
            'added_files': set(),
            'deleted_files': set()
        }
        has_results = False  # Flag pour suivre si on a des résultats
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
                    
                    # Skip PyPI version check errors
                    if "Error checking pypi for new version" in line:
                        continue
                    
                    line = line.rstrip()
                    if not line:
                        continue
                    
                    # Skip known Aider messages
                    if any(msg in line for msg in [
                        "Can't initialize prompt toolkit",
                        "No Windows console found",
                        "aider.chat/docs/troubleshooting/edit-errors.html",
                        "[Errno 22] Invalid argument"
                    ]):
                        continue
                        
                    # Si c'est une nouvelle ligne de commit, sauvegarder la ligne complète
                    if line.startswith("Commit "):
                        current_commit = line
                        full_output.append(line)
                        # Marquer qu'on a des résultats si le commit est parsé avec succès
                        if self._parse_commit_line(current_commit):
                            has_results = True
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
                    elif self._is_error_message(line):
                        # Skip PyPI version check errors
                        if not "Error checking pypi for new version" in line:
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
            return_code = process.wait()
            
            # Combine output
            output = "\n".join(full_output)
            
            # Parse changes and errors
            changes = self._parse_file_changes(output)
            errors = self._parse_error_messages(output)
            
            # Filter out PyPI version check errors and known Aider messages
            errors = [err for err in errors if not any(msg in err for msg in [
                "Error checking pypi for new version",
                "Can't initialize prompt toolkit",
                "No Windows console found",
                "aider.chat/docs/troubleshooting/edit-errors.html",
                "[Errno 22] Invalid argument"
            ])]
            
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
            # Detect team from current directory
            current_dir = os.getcwd()
            team_dirs = [d for d in os.listdir(current_dir) if d.startswith('team_')]
            team_name = team_dirs[0][5:] if team_dirs else 'default'

            # Vérifier que c'est bien une ligne de commit
            if not line or not line.startswith("Commit "):
                return True  # Return True even for non-commit lines
                
            # Extraire le hash et le message complet
            parts = line.split(maxsplit=2)
            if len(parts) < 3:
                return True  # Return True for malformed lines
                
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
                    
            # Get icon and format commit type
            icon = self.COMMIT_ICONS.get(commit_type, '🔨')
            commit_type_str = f"[{commit_type}]" if commit_type else ""

            # Log with team name
            self.logger.log(
                f"[{team_name}] [{self.agent_name}] {icon} {commit_type_str} {message}",
                'success'
            )
            
            # NEW: Generate commit log without committing
            try:
                from utils.generate_commit_log import generate_commit_log
                generate_commit_log(commit=False)  # Pass commit=False to prevent auto-commit
            except Exception as e:
                self.logger.log(f"Error generating commit log: {str(e)}", 'warning')
            
            return True  # Always return True to prevent shutdown
            
        except Exception as e:
            self.logger.log(f"Error parsing commit: {str(e)}", 'error')
            return True  # Return True even on error
