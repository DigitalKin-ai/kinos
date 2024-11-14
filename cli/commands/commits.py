"""Commit log management commands"""
import click
from utils.generate_commit_log import generate_commit_log
from utils.logger import Logger

logger = Logger()

@click.group()
def commits():
    """Manage commit logs"""
    pass

@commits.command()
def generate():
    """Generate commit log from Git history"""
    try:
        generate_commit_log()
    except Exception as e:
        logger.log(f"Error generating commit log: {str(e)}", 'error')
