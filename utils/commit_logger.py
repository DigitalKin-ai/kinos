"""Commit logging utilities"""
import re
from datetime import datetime
from typing import Optional, List, Dict
from utils.logger import Logger
from utils.constants import COMMIT_ICONS

class CommitLogger:
    """Parse and log commit messages from Aider output"""
    
    def __init__(self, logger: Optional[Logger] = None):
        """Initialize with optional logger"""
        self.logger = logger or Logger()
        self.commit_pattern = re.compile(
            r"Commit\s+([a-f0-9]+)\s+((?:feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert|merge|update|add|remove|move|cleanup|format|optimize):\s+.*)"
        )

    def parse_commits(self, output: str, agent_name: str) -> List[Dict]:
        """
        Parse commit messages from Aider output
        
        Args:
            output: Complete Aider output text
            agent_name: Name of agent that made the commits
            
        Returns:
            List of parsed commit dictionaries
        """
        commits = []
        
        try:
            # Process each line
            for line in output.splitlines():
                commit = self._parse_commit_line(line, agent_name)
                if commit:
                    commits.append(commit)
                    self._log_commit(commit)
                    
            return commits
            
        except Exception as e:
            self.logger.log(f"Error parsing commits: {str(e)}", 'error')
            return []

    def _parse_commit_line(self, line: str, agent_name: str) -> Optional[Dict]:
        """
        Parse a single commit line
        
        Args:
            line: Line of output to parse
            agent_name: Name of agent that made the commit
            
        Returns:
            Optional[Dict]: Parsed commit info or None
        """
        try:
            # Check for commit line
            match = self.commit_pattern.search(line)
            if not match:
                return {
                    'hash': 'skipped',
                    'message': 'Non-commit line', 
                    'agent': agent_name,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'skipped'
                }
                
            # Extract commit hash and full message
            commit_hash = match.group(1)
            full_message = match.group(2)
            
            # Split type and message
            commit_type, message = full_message.split(':', 1)
            commit_type = commit_type.lower()
            message = message.strip()
            
            # Get emoji for commit type
            emoji = COMMIT_ICONS.get(commit_type, '🔨')
            
            # Build commit info with status
            commit = {
                'hash': commit_hash,
                'type': commit_type,
                'message': message,
                'emoji': emoji,
                'agent': agent_name,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
            return commit
            
        except Exception as e:
            self.logger.log(f"Error parsing commit line: {str(e)}", 'error')
            return {
                'hash': 'error',
                'message': str(e),
                'agent': agent_name,
                'timestamp': datetime.now().isoformat(),
                'status': 'error'
            }

    def _log_commit(self, commit: Dict) -> None:
        """
        Log a parsed commit
        
        Args:
            commit: Parsed commit dictionary
        """
        try:
            # Format commit message
            message = (
                f"{commit['emoji']} [{commit['type']}]: {commit['message']}"
            )
            
            # Log to console
            self.logger.log(message, 'info')
            
            # Log to commits file
            self._write_commit_log(commit)
            
        except Exception as e:
            self.logger.log(f"Error logging commit: {str(e)}", 'error')

    def _write_commit_log(self, commit: Dict) -> None:
        """
        Write commit to log file
        
        Args:
            commit: Commit info to log
        """
        try:
            import os
            import json
            
            # Get log file path
            log_dir = os.path.join(os.getcwd(), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'commits.jsonl')
            
            # Append commit as JSON line
            with open(log_file, 'a', encoding='utf-8') as f:
                json.dump(commit, f)
                f.write('\n')
                
        except Exception as e:
            self.logger.log(f"Error writing commit log: {str(e)}", 'error')

    def get_commit_history(self, agent_name: Optional[str] = None) -> List[Dict]:
        """
        Get commit history, optionally filtered by agent
        
        Args:
            agent_name: Optional agent name to filter by
            
        Returns:
            List of commit dictionaries
        """
        try:
            import os
            import json
            
            commits = []
            log_file = os.path.join(os.getcwd(), 'logs', 'commits.jsonl')
            
            if not os.path.exists(log_file):
                return []
                
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        commit = json.loads(line)
                        if not agent_name or commit['agent'] == agent_name:
                            commits.append(commit)
                    except:
                        continue
                        
            return commits
            
        except Exception as e:
            self.logger.log(f"Error getting commit history: {str(e)}", 'error')
            return []
