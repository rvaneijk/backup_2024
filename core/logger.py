import logging
from datetime import datetime
from .config import LOG_DIR

def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_DIR / f"backup_{datetime.now():%Y%m%d}.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)