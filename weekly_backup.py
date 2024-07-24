#!/usr/bin/env python3
"""
Weekly Backup Script

This script performs weekly backup operations, including Git repository updates
and folder backups. It uses configuration settings from the core.config module
and leverages various utility functions from the core package.

The script performs the following main operations:
1. Sets up logging
2. Checks if the backup destination is mounted
3. Verifies the presence of the backup password environment variable
4. Displays available disk space before backup
5. Performs Git operations on specified directories
6. Backs up specified folders

Usage:
    Ensure the BACKUP_PASSWORD_ENV environment variable is set before running:
    $ export BACKUP_PASSWORD_ENV='your_secure_password'
    $ python weekly_backup.py [--debug]

Options:
    --debug     Enable debug logging (default: INFO level logging)
    --help      Show this help message and exit

Dependencies:
    - core package (config, logger, file_system, git_handler, backup_handler, utils)
    - os, sys, subprocess, argparse (standard library)

Exit codes:
    0: Success
    1: Error (check logs for details)
"""

import os
import sys
import subprocess
import argparse
from typing import NoReturn
from core.config import (
    AWS_DIR, WEEKLY_BACKUP_TYPE, WEEKLY_FREQUENCY,
    WEEKLY_BACKUP_FOLDERS, GIT_DIRS, BACKUP_PASSWORD_ENV
)
from core.logger import setup_logging
from core.file_system import check_mount
from core.git_handler import git_operations
from core.backup_handler import backup_folder
from core.utils import timer

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Weekly Backup Script")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()

def main() -> NoReturn:
    """
    Main function to execute the weekly backup process.

    This function orchestrates the entire backup process, including:
    - Setting up logging
    - Checking if the backup destination is mounted
    - Verifying the presence of the backup password environment variable
    - Displaying available disk space before backup
    - Performing Git operations on specified directories
    - Backing up specified folders

    The function will exit with a non-zero status code if any step fails.

    Raises:
        SystemExit: If any step of the backup process fails.
    """
    args = parse_arguments()
    logger = setup_logging(WEEKLY_BACKUP_TYPE, WEEKLY_FREQUENCY, args.debug)
    start_time = timer()
    logger.info("Starting weekly backup process...")
    logger.info("Use --debug option for more detailed logging if needed.")
    
    if not check_mount():
        logger.error("Failed to access the backup destination. Exiting.")
        sys.exit(1)
    
    if BACKUP_PASSWORD_ENV not in os.environ:
        logger.error(f"Error: {BACKUP_PASSWORD_ENV} environment variable is not set")
        logger.info(f"To run this script, set the {BACKUP_PASSWORD_ENV} environment variable:")
        logger.info(f"export {BACKUP_PASSWORD_ENV}='your_secure_password'")
        sys.exit(1)
    
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
    
    end_time = timer(start_time)
    logger.info(f"Weekly backup process completed. Total duration: {end_time}")
    logger.info("For more detailed logs, use the --debug option when running the script.")
    logger.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        args = parse_arguments()
        logger = setup_logging(WEEKLY_BACKUP_TYPE, WEEKLY_FREQUENCY, args.debug)
        logger.exception("An unexpected error occurred:")
        sys.exit(1)