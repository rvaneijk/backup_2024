import os
import sys
import subprocess
from core.config import load_config, AWS_DIR
from core.logger import setup_logging
from core.file_system import check_mount
from core.backup_handler import backup_folder
from core.utils import timer

logger = setup_logging()

def get_folders_to_skip(backup_folders):
    print("Select folders to skip (enter the number, separated by spaces):")
    for i, folder in enumerate(backup_folders, 1):
        print(f"{i}. {folder['dest']}")
    skip_input = input("Enter numbers to skip (or press Enter to backup all): ")
    skip_numbers = [int(num) for num in skip_input.split() if num.isdigit()]
    return set(skip_numbers)

def main():
    start_time = timer()
    logger.info("Starting monthly backup process...")
    
    config = load_config('configs/monthly_config.yaml')
    
    check_mount()
    
    if "BACKUP_PASSWORD" not in os.environ:
        logger.error("Error: BACKUP_PASSWORD environment variable is not set")
        logger.info("To run this script, set the BACKUP_PASSWORD environment variable:")
        logger.info("export BACKUP_PASSWORD='your_secure_password'")
        sys.exit(1)
    
    logger.info("DISK space on the device before backup:")
    subprocess.run(["df", "-h", "--total", str(AWS_DIR)])
    
    if config.get('allow_skip', False):
        folders_to_skip = get_folders_to_skip(config['backup_folders'])
    else:
        folders_to_skip = set()
    
    logger.info("Starting backup operations...")
    for i, folder in enumerate(config['backup_folders'], 1):
        if i in folders_to_skip:
            logger.info(f"Skipping {folder['dest']}...")
            continue
        logger.info(f"Backing up {folder['dest']}...")
        if not backup_folder(folder['dest'], folder['source'], folder['exclude'], 
                             backup_type="MONTHLY", archive_name=folder['archive_name']):
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
        logger.exception("An unexpected error occurred:")
        sys.exit(1)