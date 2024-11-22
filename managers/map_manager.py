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
    def _analyze_folder_structure(self, mission_content, objective_content):
        """
        Analyze current folder structure and generate map.
        
        Args:
            mission_content (str): Content of mission file
            objective_content (str): Content of objective file
            
        Returns:
            str: Generated folder map content
        """
        try:
            # Get current working directory
            current_dir = os.getcwd()
            
            # Generate complete tree structure
            tree_structure = self._generate_tree_structure()
            
            # Get folder analysis from GPT
            client = openai.OpenAI()
            prompt = self._create_map_prompt(
                current_dir,
                tree_structure,
                mission_content,
                objective_content
            )
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a technical architect analyzing project folder structures and file organization."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"Failed to analyze folder structure: {str(e)}")
            raise
