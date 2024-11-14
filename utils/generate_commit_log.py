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
    """Get git log with format: hash, author, date, message"""
    try:
        cmd = [
            'git', 'log',
            '--pretty=format:%H|%an|%ad|%s',
            '--date=iso'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        print(f"Error getting git log: {str(e)}")
        return ""

def parse_commit_message(message: str) -> tuple:
    """Parse commit message to extract type and description"""
    # Check for known commit types
    for commit_type in COMMIT_ICONS:
        if message.lower().startswith(f"{commit_type}:"):
            return commit_type, message[len(commit_type)+1:].strip()
    return None, message

def format_commit_line(hash: str, author: str, date: str, message: str) -> str:
    """Format a commit line with icon"""
    try:
        # Parse date to datetime
        dt = datetime.fromisoformat(date.replace(' ', 'T'))
        formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Get commit type and icon
        commit_type, description = parse_commit_message(message)
        icon = COMMIT_ICONS.get(commit_type, '🔨')
        
        # Format line
        return f"- {formatted_date} [{author}] {icon} {hash[:7]}: {description}"
    except Exception as e:
        print(f"Error formatting commit: {str(e)}")
        return f"- {date} {hash[:7]}: {message}"

def generate_commit_log():
    """Generate commit.md from git history"""
    logger = Logger()
    try:
        logger.log("Generating commit log...", 'info')
        
        # Get git log
        git_log = get_git_log()
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
                formatted = format_commit_line(hash, author, date, message)
                commits.append(formatted)
            except Exception as e:
                logger.log(f"Error parsing commit line: {str(e)}", 'error')
                continue
                
        # Write to commit.md
        with open('commit.md', 'w', encoding='utf-8') as f:
            f.write("# Git Commit History\n\n")
            f.write("\n".join(reversed(commits)))  # Newest first
            
        logger.log(f"Generated commit.md with {len(commits)} commits", 'success')
        
    except Exception as e:
        logger.log(f"Error generating commit log: {str(e)}", 'error')

if __name__ == "__main__":
    generate_commit_log()
