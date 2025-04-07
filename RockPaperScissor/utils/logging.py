"""
Logging configuration module for RockPaperScissor game.
Sets up logging for the application.
"""
import logging
import os
import sys
from pathlib import Path

def setup_logging():
    """
    Configure logging settings for the application
    
    Returns:
        logging.Logger: Logger for the RockPaperScissor application
    """
    # Determine log level from environment variable or use default
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level, None)
    
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)  # Log to stdout for CloudWatch
        ]
    )
    
    # Create logger for our application
    logger = logging.getLogger("RockPaperScissor")
    
    # Reduce noise from boto3 and other libraries
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Create log file if in development environment
    if os.environ.get("AWS_ENV") != "production":
        # Ensure logs directory exists
        logs_dir = Path("./logs")
        if not logs_dir.exists():
            logs_dir.mkdir(parents=True)
        
        # Add file handler for development
        file_handler = logging.FileHandler("./logs/app.log")
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(file_handler)
        
        # Add error file handler
        error_handler = logging.FileHandler("./logs/error.log")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(error_handler)
    
    return logger