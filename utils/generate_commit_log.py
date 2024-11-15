"""
Script to generate commit.md from Git history
"""
import os
import sys
from pathlib import Path
import subprocess
from datetime import datetime

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.logger import Logger

# Commit type icons mapping
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

def get_git_log() -> str:
    """Get git log with format: hash, author, date, message and numstat"""
    try:
        # First get the log entries - add --all to get all commits
        cmd = [
            'git', 'log',
            '--all',  # Get all commits from all branches
            '--pretty=format:%H|%an|%ad|%s',
            '--date=iso'
        ]
        # Add UTF-8 encoding handling
        log_result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            encoding='utf-8'  # Explicitly specify UTF-8
        )
        
        # Then get the numstat for all commits
        cmd_stats = [
            'git', 'log',
            '--all',  # Get all commits from all branches
            '--pretty=format:%H',  # Just the hash
            '--numstat'  # Get number statistics
        ]
        # Add UTF-8 encoding handling
        stats_result = subprocess.run(
            cmd_stats, 
            capture_output=True, 
            text=True,
            encoding='utf-8'  # Explicitly specify UTF-8
        )
        
        # Create a mapping of commit hash to stats
        stats_map = {}
        current_hash = None
        current_stats = []
        
        for line in stats_result.stdout.split('\n'):
            if line.strip():
                if len(line) == 40:  # This is a hash
                    if current_hash:
                        # Calculate total changes for previous commit
                        added = sum(int(s[0]) for s in current_stats if s[0].isdigit())
                        deleted = sum(int(s[1]) for s in current_stats if s[1].isdigit())
                        stats_map[current_hash] = (added, deleted)
                    current_hash = line
                    current_stats = []
                else:
                    # Parse stats line: additions, deletions, filename
                    parts = line.split('\t')
                    if len(parts) == 3:
                        current_stats.append((parts[0], parts[1]))
        
        # Don't forget the last commit
        if current_hash and current_stats:
            added = sum(int(s[0]) for s in current_stats if s[0].isdigit())
            deleted = sum(int(s[1]) for s in current_stats if s[1].isdigit())
            stats_map[current_hash] = (added, deleted)
        
        return log_result.stdout, stats_map
        
    except Exception as e:
        print(f"Error getting git log: {str(e)}")
        return "", {}

def parse_commit_message(message: str) -> tuple:
    """Parse commit message to extract type and description"""
    # Check for known commit types
    for commit_type in COMMIT_ICONS:
        if message.lower().startswith(f"{commit_type}:"):
            return commit_type, message[len(commit_type)+1:].strip()
    return None, message

def format_commit_line(hash: str, author: str, date: str, message: str, stats_map: dict) -> str:
    """Format a commit line with icon and change statistics"""
    try:
        # Parse date to datetime
        dt = datetime.fromisoformat(date.replace(' ', 'T'))
        formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Get commit type and icon
        commit_type, description = parse_commit_message(message)
        icon = COMMIT_ICONS.get(commit_type, '🔨')
        
        # Get stats if available
        stats = stats_map.get(hash, (0, 0))
        stats_text = f" (+{stats[0]}, -{stats[1]} chars)" if stats[0] or stats[1] else ""
        
        # Format line
        return f"- {formatted_date} [{author}] {icon} {hash[:7]}: {description}{stats_text}"
    except Exception as e:
        print(f"Error formatting commit: {str(e)}")
        return f"- {date} {hash[:7]}: {message}"

def generate_commit_log(commit: bool = False):
    """Generate commits.md from git history"""
    logger = Logger()
    try:
        # Use current directory
        current_dir = os.getcwd()
        
        # Verify it's a git repository
        if not os.path.exists(os.path.join(current_dir, '.git')):
            logger.log("Not a git repository", 'error')
            return
            
        logger.log("Generating commit log...", 'info')
        
        # Get git log and stats
        git_log, stats_map = get_git_log()
        if not git_log:
            logger.log("No git history found", 'error')
            return
            
        # Parse and format commits
        commits = []
        for line in git_log.split('\n'):
            if not line:
                continue
            try:
                hash, author, date, message = line.split('|')
                formatted = format_commit_line(hash, author, date, message, stats_map)
                commits.append(formatted)
            except Exception as e:
                logger.log(f"Error parsing commit line: {str(e)}", 'error')
                continue
                
        # Write to commits.md
        with open('commits.md', 'w', encoding='utf-8') as f:
            f.write("# Git Commit History\n\n")
            f.write("\n".join(reversed(commits)))  # Newest first
            
        # Optional commit step
        if commit:
            try:
                subprocess.run(['git', 'add', 'commits.md'], check=True)
                subprocess.run(['git', 'commit', '-m', '📝 update: Regenerate commit history'], check=True)
                logger.log("Committed commits.md to repository", 'success')
            except subprocess.CalledProcessError as e:
                logger.log(f"Error committing commits.md: {str(e)}", 'error')
        
        logger.log(f"Generated commits.md with {len(commits)} commits", 'success')
        
    except Exception as e:
        logger.log(f"Error generating commit log: {str(e)}", 'error')

if __name__ == "__main__":
    generate_commit_log()
