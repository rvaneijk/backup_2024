import logging
import sys
from datetime import datetime
from pathlib import Path
from .config import LOG_DIR

def setup_logging(backup_type, backup_frequency):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"{datetime.now():%y%m%d}_{backup_type}_{backup_frequency}.log"
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%y%m%d %H:%M:%S')

    file_handler = logging.FileHandler(log_file, mode='a', delay=False)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )
    
    logger = logging.getLogger(__name__)
    
    # Check if the file is empty (new file) or has content
    if log_file.stat().st_size == 0:
        log_message = f"Logging started ({log_file})"
        logger.info(log_message)
    else:
        logger.info(f"Appending to existing log file ({log_file})")
    
    return logger