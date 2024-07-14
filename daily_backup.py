import os
import sys
import subprocess
from core.config import (
    AWS_DIR, DAILY_BACKUP_TYPE, DAILY_FREQUENCY,
    DAILY_BACKUP_FOLDERS, GIT_DIRS, BACKUP_PASSWORD_ENV
)
from core.logger import setup_logging
from core.file_system import check_mount
from core.git_handler import git_operations
from core.backup_handler import backup_folder
from core.utils import timer

def main():
    logger = setup_logging(DAILY_BACKUP_TYPE, DAILY_FREQUENCY)
    start_time = timer()
    logger.info("Starting daily backup process...")
    
    check_mount()
    
    if BACKUP_PASSWORD_ENV not in os.environ:
        logger.error(f"Error: {BACKUP_PASSWORD_ENV} environment variable is not set")
        logger.info(f"To run this script, set the {BACKUP_PASSWORD_ENV} environment variable:")
        logger.info(f"export {BACKUP_PASSWORD_ENV}='your_secure_password'")
        sys.exit(1)
    
    logger.info("Starting Git operations...")
    for dir_path in GIT_DIRS:
        if not git_operations(dir_path):
            logger.error(f"Git operations failed for {dir_path}. Exiting.")
            sys.exit(1)

    logger.info("Starting backup operations...")
    for folder in DAILY_BACKUP_FOLDERS:
        logger.info(f"Backing up {folder['source']}...")
        if not backup_folder(
            folder['dest'], 
            folder['source'], 
            folder['exclude'], 
            backup_type=DAILY_BACKUP_TYPE, 
            archive_name=folder['archive_name']
        ):
            logger.error(f"Backup failed for {folder['archive_name']}. Exiting.")
            sys.exit(1)
    
    logger.info("DISK space on the device:")
    subprocess.run(["df", "-h", "--total", str(AWS_DIR)])
    
    logger.info("TOTAL Size of the archive:")
    subprocess.run(f"du -h -c {AWS_DIR} | grep total$", shell=True)
    
    elapsed_time = timer(start_time)
    logger.info(f"Daily backup completed. Duration: {elapsed_time}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger = setup_logging(DAILY_BACKUP_TYPE, DAILY_FREQUENCY)
        logger.exception("An unexpected error occurred:")
        sys.exit(1)