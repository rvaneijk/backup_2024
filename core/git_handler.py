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
    logger.info(f"Current working directory: {os.getcwd()}")
    
    try:
        # Log Git status before operations
        logger.info("Git status before operations:")
        status_before = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        logger.info(status_before.stdout.strip() if status_before.stdout.strip() else "No changes")

        # Add all changes
        logger.info("Adding all changes...")
        add_result = subprocess.run(["git", "add", "."], capture_output=True, text=True, check=True)
        logger.info(f"Git add output: {add_result.stdout.strip()}")

        # Check if there are changes to commit
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        
        if status.stdout.strip():
            # Changes exist, proceed with commit
            logger.info("Changes detected. Proceeding with commit...")
            commit_message = datetime.now().strftime("%y%m%d %H:%M")
            commit_result = subprocess.run(["git", "commit", "-m", commit_message], capture_output=True, text=True, check=True)
            logger.info(f"Commit result: {commit_result.stdout.strip()}")
            logger.info(f"Changes committed in {dir_path}")
        else:
            # No changes to commit
            logger.info(f"No changes to commit in {dir_path}")
        
        # Show detailed status after operations
        logger.info("Git status after operations:")
        status_after = subprocess.run(["git", "status"], capture_output=True, text=True, check=True)
        logger.info(status_after.stdout.strip())

        # Log last commit
        last_commit = subprocess.run(["git", "log", "-1", "--oneline"], capture_output=True, text=True, check=True)
        logger.info(f"Last commit: {last_commit.stdout.strip()}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed in {dir_path}: {e}")
        logger.error(f"Command output: {e.output}")
        return False
    
    return True