"""Logger Configuration"""

import logging
import os
from datetime import datetime

def setup_logger(name: str, log_level=logging.INFO) -> logging.Logger:
    """
    Setup logger with file and console handlers
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # File handler
    log_file = f"logs/ats_resume_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger
