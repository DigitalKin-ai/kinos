import os
import asyncio
import random
import subprocess
import logging
from pathlib import Path
import fnmatch
from utils.logger import Logger
import openai
import tiktoken
from dotenv import load_dotenv

class MapManager:
    """Manager class for generating context maps for agent operations."""