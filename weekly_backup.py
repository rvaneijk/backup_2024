import os
import sys
import subprocess
from core.config import load_config, AWS_DIR
from core.logger import setup_logging
from core.file_system import check_mount
from core.backup_handler import backup_folder
from core.utils import timer

logger = setup_logging()

def main():
    start_time = timer()
    logger.info("Starting weekly backup process...")
    
    config = load_config('configs/weekly_config.yaml')
    
    check_mount()
    
    if "BACKUP_PASSWORD" not in os.environ:
        logger.error("Error: BACKUP_PASSWORD environment variable is not set")
        logger.info("To run this script, set the BACKUP_PASSWORD environment variable:")
        logger.info("export BACKUP_PASSWORD='your_secure_password'")
        sys.exit(1)
    
    logger.info("Starting backup operations...")
    for folder in config['backup_folders']:
        logger.info(f"Backing up {folder['dest']}...")
        if not backup_folder(folder['dest'], folder['source'], folder['exclude'], backup_type="WEEKLY"):
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
        logger.exception("An unexpected error occurred:")
        sys.exit(1)