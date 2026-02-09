import logging
import sys
from datetime import datetime
from pathlib import Path

# Create logs directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name: str, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    
    # File handler
    log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}_khanoos.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(console_formatter)
    
    # Error handler
    error_log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}_errors.log"
    error_handler = logging.FileHandler(error_log_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(console_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger

# Service loggers
auth_logger = setup_logger("khanoos.auth")
order_logger = setup_logger("khanoos.order")
menu_logger = setup_logger("khanoos.menu")
branch_logger = setup_logger("khanoos.branch")
restaurant_logger = setup_logger("khanoos.restaurant")
pricing_logger = setup_logger("khanoos.pricing")