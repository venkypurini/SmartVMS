import os
import logging
import config

LOGS_DIR = os.path.dirname(config.LOG_FILE)

def setup_logger():
    """Setup and configure application logger."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Set numeric level
    numeric_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("VMS")
    logger.info("Application logging initialized.")
    return logger

# Create logger instance
logger = setup_logger()
