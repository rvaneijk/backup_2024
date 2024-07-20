"""
Weekly Backup Script

This script performs weekly backup operations, including Git repository updates
and folder backups. It uses configuration settings from the core.config module
and leverages various utility functions from the core package.

The script performs the following main operations:
1. Sets up logging
2. Checks if the backup destination is mounted and attempts to mount if not
3. Verifies the presence of the backup password environment variable
4. Displays available disk space before backup
5. Performs Git operations on specified directories
6. Backs up specified folders

Usage:
    Ensure the BACKUP_PASSWORD_ENV environment variable is set before running:
    $ export BACKUP_PASSWORD_ENV='your_secure_password'
    $ python weekly_backup.py

Dependencies:
    - core package (config, logger, file_system, git_handler, backup_handler, utils)
    - os, sys, subprocess (standard library)

Exit codes:
    0: Success
    1: Error (check logs for details)
"""

import os
import sys
import subprocess
from core.config import (
    AWS_DIR, WEEKLY_BACKUP_TYPE, WEEKLY_FREQUENCY,
    WEEKLY_BACKUP_FOLDERS, GIT_DIRS, BACKUP_PASSWORD_ENV
)
from core.logger import setup_logging
from core.file_system import check_mount
from core.git_handler import git_operations
from core.backup_handler import backup_folder
from core.utils import timer

def main():
    """
    Main function to execute the weekly backup process.

    This function orchestrates the entire backup process, including:
    - Setting up logging
    - Checking if the backup destination is mounted and attempting to mount if not
    - Verifying the presence of the backup password environment variable
    - Displaying available disk space before backup
    - Performing Git operations on specified directories
    - Backing up specified folders

    The function will exit with a non-zero status code if any step fails.

    Returns:
        None
    """
    logger = setup_logging(WEEKLY_BACKUP_TYPE, WEEKLY_FREQUENCY)
    start_time = timer()
    logger.info("Starting weekly backup process...")
    
    # Check if the backup destination is mounted
    if not check_mount():
        logger.error("Backup destination is not mounted. Attempting to mount...")
        try:
            # Assuming there's a mount_backup_destination function in core.file_system
            from core.file_system import mount_backup_destination
            if not mount_backup_destination():
                logger.error("Failed to mount backup destination. Exiting.")
                sys.exit(1)
            logger.info("Backup destination mounted successfully.")
        except ImportError:
            logger.error("mount_backup_destination function not found. Please mount the destination manually.")
            sys.exit(1)
    
    # Check for backup password
    if BACKUP_PASSWORD_ENV not in os.environ:
        logger.error(f"Error: {BACKUP_PASSWORD_ENV} environment variable is not set")
        logger.info(f"To run this script, set the {BACKUP_PASSWORD_ENV} environment variable:")
        logger.info(f"export {BACKUP_PASSWORD_ENV}='your_secure_password'")
        sys.exit(1)
    
    # Display disk space information
    logger.info("DISK space on the device before backup:")
    subprocess.run(["df", "-h", "--total", str(AWS_DIR)])
    
    logger.info("Starting Git operations...")
    for dir_path in GIT_DIRS:
        if not git_operations(dir_path):
            logger.error(f"Git operations failed for {dir_path}. Exiting.")
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
    
    logger.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger = setup_logging(WEEKLY_BACKUP_TYPE, WEEKLY_FREQUENCY)
        logger.exception("An unexpected error occurred:")
        sys.exit(1)