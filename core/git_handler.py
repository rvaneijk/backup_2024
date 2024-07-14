import os
import subprocess
import logging
from datetime import datetime
from .config import BASE_DIR

logger = logging.getLogger(__name__)

def git_operations(dir_path):
    full_path = BASE_DIR / dir_path
    os.chdir(full_path)
    logger.info(f"Processing {dir_path}")
    
    try:
        # Add all changes
        subprocess.run(["git", "add", "."], check=True)
        
        # Check if there are changes to commit
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        
        if status.stdout.strip():
            # Changes exist, proceed with commit
            commit_message = datetime.now().strftime("%y%m%d %H:%M")
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            logger.info(f"Changes committed in {dir_path}")
        else:
            # No changes to commit
            logger.info(f"No changes to commit in {dir_path}")
        
        # Show status for logging purposes
        subprocess.run(["git", "status"], check=True)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed in {dir_path}: {e}")
        return False
    
    return True