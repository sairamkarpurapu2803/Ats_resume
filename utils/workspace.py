"""Workspace Initialization"""

import os
from utils.logger import setup_logger

logger = setup_logger(__name__)

def init_workspace():
    """
    Initialize required directories and configurations
    """
    directories = [
        "uploads",
        "exports",
        "logs",
        "templates",
        "cache"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Initialized directory: {directory}")
    
    logger.info("Workspace initialization completed")
