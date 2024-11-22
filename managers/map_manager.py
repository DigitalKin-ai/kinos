import os
import asyncio
import logging
from pathlib import Path
import fnmatch
from utils.logger import Logger
import openai
import tiktoken
from dotenv import load_dotenv

class MapManager:
    """
    Manager class for generating and maintaining project structure maps.
    
    Responsible for:
    - Generating hierarchical maps of project structure
    - Maintaining global project map
    - Analyzing file roles and relationships
    - Tracking structural changes
    
    Attributes:
        logger (Logger): Logging utility instance
        tokenizer (tiktoken.Encoding): GPT tokenizer for content analysis
        api_semaphore (asyncio.Semaphore): Rate limiter for API calls
    """
    
    def __init__(self):
        """Initialize the map manager with required components."""
        self.logger = Logger()
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        self.api_semaphore = asyncio.Semaphore(10)
