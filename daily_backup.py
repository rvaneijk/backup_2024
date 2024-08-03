#!/usr/bin/env python3
"""
Daily Backup Script

This script performs daily backup operations, including Git repository updates
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
    $ python daily_backup.py [--debug] [--compression-level LEVEL]

Options:
    --debug     Enable debug logging (default: INFO level logging)
    --compression-level LEVEL : Set 7-Zip compression level (e.g., -mx0 to -mx9, default: -mx5)
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
from core.config import (
    AWS_DIR, DAILY_BACKUP_TYPE, DAILY_FREQUENCY,
    DAILY_BACKUP_FOLDERS, GIT_DIRS, BACKUP_PASSWORD_ENV,
    SEVEN_ZIP_COMPRESSION_LEVEL, DEFAULT_COMPRESSION_LEVEL
)
from core.logger import setup_logging
from core.file_system import check_mount
from core.git_handler import git_operations
from core.backup_handler import backup_folder
from core.utils import timer

def parse_arguments():
    parser = argparse.ArgumentParser(description="Daily Backup Script")
    parser.add_argument("--archive", action="store_true", help="Run the archive task")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--compression-level", type=str, default=SEVEN_ZIP_COMPRESSION_LEVEL,
                        help=f"7-Zip compression level (e.g., -mx0 to -mx9, default: {SEVEN_ZIP_COMPRESSION_LEVEL})")
    return parser.parse_args()

def archive_task(logger, compression_level):
    """Perform the archive task (daily backup)."""
    start_time = timer()
    logger.info("Starting daily backup process...")
    
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
    for folder in DAILY_BACKUP_FOLDERS:
        logger.info(f"Backing up {folder['source']}...")
        if not backup_folder(
            folder['dest'], 
            folder['source'], 
            folder['exclude'], 
            backup_type=DAILY_BACKUP_TYPE,
            archive_name=folder['archive_name'],
            compression_level=compression_level
        ):
            logger.error(f"Backup failed for {folder['archive_name']}. Exiting.")
            sys.exit(1)
    
    end_time = timer(start_time)
    logger.info(f"Daily backup process completed. Total duration: {end_time}")

def main():
    args = parse_arguments()
    compression_level = args.compression_level
    logger = setup_logging(DAILY_BACKUP_TYPE, DAILY_FREQUENCY, args.debug)
    
    logger.info("Starting daily backup process...")
    logger.info("Use --debug option for more detailed logging if needed.")
    logger.info(f"Using 7-Zip compression level: {compression_level}")
    logger.info(f"Default compression level is: {DEFAULT_COMPRESSION_LEVEL}")
    
    archive_task(logger, compression_level)
    
    logger.info("For more detailed logs, use the --debug option when running the script.")
    logger.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        args = parse_arguments()
        logger = setup_logging(DAILY_BACKUP_TYPE, DAILY_FREQUENCY, args.debug)
        logger.exception("An unexpected error occurred:")
        sys.exit(1)