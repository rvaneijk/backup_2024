import os
import sys
import subprocess
from core.config import (
    AWS_DIR, MONTHLY_BACKUP_TYPE, MONTHLY_FREQUENCY,
    MONTHLY_BACKUP_FOLDERS, BACKUP_PASSWORD_ENV, ALLOW_SKIP_MONTHLY
)
from core.logger import setup_logging
from core.file_system import check_mount
from core.backup_handler import backup_folder
from core.utils import timer

def get_folders_to_skip(backup_folders):
    print("Select folders to skip (enter the number, separated by spaces):")
    for i, folder in enumerate(backup_folders, 1):
        print(f"{i}. {folder['archive_name']}")
    skip_input = input("Enter numbers to skip (or press Enter to backup all): ")
    skip_numbers = [int(num) for num in skip_input.split() if num.isdigit()]
    return set(skip_numbers)

def main():
    logger = setup_logging(MONTHLY_BACKUP_TYPE, MONTHLY_FREQUENCY)
    start_time = timer()
    logger.info("Starting monthly backup process...")
    
    check_mount()
    
    if BACKUP_PASSWORD_ENV not in os.environ:
        logger.error(f"Error: {BACKUP_PASSWORD_ENV} environment variable is not set")
        logger.info(f"To run this script, set the {BACKUP_PASSWORD_ENV} environment variable:")
        logger.info(f"export {BACKUP_PASSWORD_ENV}='your_secure_password'")
        sys.exit(1)
    
    logger.info("DISK space on the device before backup:")
    subprocess.run(["df", "-h", "--total", str(AWS_DIR)])
    
    if ALLOW_SKIP_MONTHLY:
        folders_to_skip = get_folders_to_skip(MONTHLY_BACKUP_FOLDERS)
    else:
        folders_to_skip = set()
    
    logger.info("Starting backup operations...")
    for i, folder in enumerate(MONTHLY_BACKUP_FOLDERS, 1):
        if i in folders_to_skip:
            logger.info(f"Skipping {folder['archive_name']}...")
            continue
        logger.info(f"Backing up {folder['source']}...")
        if not backup_folder(
            folder['dest'], 
            folder['source'], 
            folder['exclude'], 
            backup_type=MONTHLY_BACKUP_TYPE, 
            archive_name=folder['archive_name']
        ):
            logger.error(f"Backup failed for {folder['archive_name']}. Exiting.")
            sys.exit(1)
    
    logger.info("DISK space on the device after backup:")
    subprocess.run(["df", "-h", "--total", str(AWS_DIR)])
    
    logger.info("TOTAL Size of the archive:")
    subprocess.run(f"du -h -c {AWS_DIR} | grep total$", shell=True)
    
    elapsed_time = timer(start_time)
    logger.info(f"Monthly backup completed. Duration: {elapsed_time}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger = setup_logging(MONTHLY_BACKUP_TYPE, MONTHLY_FREQUENCY)
        logger.exception("An unexpected error occurred:")
        sys.exit(1)