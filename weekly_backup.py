import os
import sys
import subprocess
from core.config import (
    AWS_DIR, WEEKLY_BACKUP_TYPE, WEEKLY_FREQUENCY,
    WEEKLY_BACKUP_FOLDERS, BACKUP_PASSWORD_ENV
)
from core.logger import setup_logging
from core.file_system import check_mount, unmount
from core.backup_handler import backup_folder
from core.utils import timer

def main():
    logger = setup_logging(WEEKLY_BACKUP_TYPE, WEEKLY_FREQUENCY)
    start_time = timer()
    logger.info("Starting weekly backup process...")
    
    check_mount()
    
    if BACKUP_PASSWORD_ENV not in os.environ:
        logger.error(f"Error: {BACKUP_PASSWORD_ENV} environment variable is not set")
        logger.info(f"To run this script, set the {BACKUP_PASSWORD_ENV} environment variable:")
        logger.info(f"export {BACKUP_PASSWORD_ENV}='your_secure_password'")
        sys.exit(1)
    
    logger.info("Starting backup operations...")
    for folder in WEEKLY_BACKUP_FOLDERS:
        logger.info(f"Backing up {folder['source']}...")
        if not backup_folder(
            folder['dest'], 
            folder['source'], 
            folder['exclude'], 
            backup_type=WEEKLY_BACKUP_TYPE, 
            archive_name=folder['archive_name']
        ):
            logger.error(f"Backup failed for {folder['archive_name']}. Exiting.")
            sys.exit(1)
    
    logger.info("DISK space on the device:")
    subprocess.run(["df", "-h", "--total", str(AWS_DIR)])
    
    logger.info("TOTAL Size of the archive:")
    subprocess.run(f"du -h -c {AWS_DIR} | grep total$", shell=True)
    
    elapsed_time = timer(start_time)
    logger.info(f"Weekly backup completed. Duration: {elapsed_time}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger = setup_logging(WEEKLY_BACKUP_TYPE, WEEKLY_FREQUENCY)
        logger.exception("An unexpected error occurred:")
        sys.exit(1)
    finally:
        unmount()