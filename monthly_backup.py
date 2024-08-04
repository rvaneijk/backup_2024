#!/usr/bin/env python3
"""
Integrated Monthly Backup Script

This script performs monthly backup operations and optional PAR file creation.
It combines the functionality of archiving and PAR file creation into a single
script with command-line options to control execution.

Features:
- Monthly backup of specified folders
- Optional PAR2 file creation for existing backups
- Git operations on specified directories
- Logging of all operations
- Disk space checking before backup
- Automatic mounting of backup destination (if not already mounted)
- Configurable 7-Zip compression level
- Optimized PAR2 file creation strategy

Usage:
    For archive task only:
    $ python monthly_backup.py --archive [--debug] [--compression-level LEVEL]

    For PAR file creation task only:
    $ python monthly_backup.py --par YYMMDD [--debug]

    where YYMMDD is the date of the backup in YYMMDD format.

Arguments:
    --archive : Run the archive (backup) task
    --par YYMMDD : Run the PAR file creation task
    --debug : Enable debug logging (default: INFO level logging)
    --compression-level LEVEL : Set 7-Zip compression level (e.g., -mx0 to -mx9, default: -mx5)
    --help : Show this help message and exit

Environment Variables:
    BACKUP_PASSWORD_ENV: Must be set for the archive task (contains the backup password)

Dependencies:
    - core package (config, logger, file_system, backup_handler, utils, git_handler, par_handler)
    - Standard libraries: os, sys, subprocess, argparse, datetime, yaml
    - External: par2 command-line tool (for PAR task)

Exit codes:
    0: Success
    1: Error (check logs for details)
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime
import yaml

from core.config import (
    AWS_DIR, MONTHLY_BACKUP_TYPE, MONTHLY_FREQUENCY,
    MONTHLY_BACKUP_FOLDERS, BACKUP_PASSWORD_ENV, ALLOW_SKIP_MONTHLY,
    MONTHLY_CONFIG, GIT_DIRS, SEVEN_ZIP_COMPRESSION_LEVEL, DEFAULT_COMPRESSION_LEVEL
)
from core.logger import setup_logging
from core.file_system import check_mount, ensure_dir_exists
from core.backup_handler import backup_folder
from core.utils import timer
from core.git_handler import git_operations
from core import par_handler

def run_command(command):
    """Execute a shell command and return its success status."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: Command failed with error: {result.stderr}")
    return result.returncode == 0

def get_items_to_skip(items, skip_prompt):
    """Prompt the user to select items to skip during processing."""
    print(skip_prompt)
    for i, item in enumerate(items, 1):
        print(f"{i}. {item['archive_name']}")
    skip_input = input("Enter numbers to skip (or press Enter to process all): ")
    skip_numbers = [int(num) for num in skip_input.split() if num.isdigit()]
    return set(skip_numbers)

def load_config(config_file):
    """Load configuration from a YAML file."""
    try:
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as e:
        print(f"Error parsing config file: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Config file not found: {config_file}")
        sys.exit(1)

def archive_task(logger, compression_level):
    """Perform the archive task (monthly backup)."""
    start_time = timer()
    logger.info("Starting monthly backup process...")
    
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
    
    # Perform Git operations
    logger.info("Starting Git operations...")
    for dir_path in GIT_DIRS:
        if not git_operations(dir_path):
            logger.error(f"Git operations failed for {dir_path}. Exiting.")
            sys.exit(1)
    
    if ALLOW_SKIP_MONTHLY:
        folders_to_skip = get_items_to_skip(MONTHLY_BACKUP_FOLDERS, "Select folders to skip (enter the number, separated by spaces):")
    else:
        folders_to_skip = set()
    
    logger.info("Starting backup operations...")
    for i, folder in enumerate(MONTHLY_BACKUP_FOLDERS, 1):
        if i in folders_to_skip:
            logger.info(f"Skipping {folder['archive_name']}...")
            continue
        
        # Ensure destination directory exists
        dest_dir = AWS_DIR / folder['dest']
        ensure_dir_exists(dest_dir)
        
        logger.info(f"Backing up {folder['source']}...")
        if not backup_folder(
            folder['dest'], 
            folder['source'], 
            folder['exclude'], 
            backup_type=MONTHLY_BACKUP_TYPE,
            archive_name=folder['archive_name'],
            compression_level=compression_level
        ):
            logger.error(f"Backup failed for {folder['archive_name']}. Exiting.")
            sys.exit(1)
    
    end_time = timer(start_time)
    logger.info(f"Monthly backup process completed. Total duration: {end_time}")

def par_task(logger, incr):
    """Perform the PAR task (create and verify PAR2 files) with optimized strategy."""
    config = load_config(MONTHLY_CONFIG)
    archives = config['backup_folders']
    
    logger.info(f"Found {len(archives)} archives in the configuration.")
    
    archives_to_skip = get_items_to_skip(archives, "Select archives to skip (enter the number, separated by spaces):")
    
    start_time = datetime.now()
    logger.info(f"Starting PAR file creation process... (Start time: {start_time.strftime('%y%m%d %H:%M')})")
    
    total_archives = len(archives)
    processed_archives = 0
    skipped_archives = 0
    
    for i, archive in enumerate(archives, 1):
        if i in archives_to_skip:
            logger.info(f"Skipping archive {i}/{total_archives}: {archive['archive_name']}...")
            skipped_archives += 1
            continue
        
        logger.info(f"Processing archive {i}/{total_archives}: {archive['archive_name']}")
        full_path = AWS_DIR / archive['dest']
        
        if os.path.exists(full_path):
            logger.info(f"Directory found: {full_path}")
            par_handler.process_archive(full_path, archive['archive_name'], incr, logger)
            processed_archives += 1
        else:
            logger.warning(f"Directory does not exist: {full_path}. Skipping this archive.")
            skipped_archives += 1
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("PAR file creation process summary:")
    logger.info(f"Total archives: {total_archives}")
    logger.info(f"Processed archives: {processed_archives}")
    logger.info(f"Skipped archives: {skipped_archives}")
    logger.info(f"Start time: {start_time.strftime('%y%m%d %H:%M')}")
    logger.info(f"End time: {end_time.strftime('%y%m%d %H:%M')}")
    logger.info(f"Total duration: {duration}")
    
    if processed_archives == total_archives:
        logger.info("All archives were successfully processed.")
    elif processed_archives == 0:
        logger.warning("No archives were processed. Please check your configuration and inputs.")
    else:
        logger.info(f"Processed {processed_archives} out of {total_archives} archives.")
    
    logger.info("PAR file creation process completed!")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Monthly Backup Script")
    parser.add_argument("--archive", action="store_true", help="Run the archive task")
    parser.add_argument("--par", help="Run the PAR file creation task. Requires a date value in YYMMDD format.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--compression-level", type=str, default=SEVEN_ZIP_COMPRESSION_LEVEL,
                        help=f"7-Zip compression level (e.g., -mx0 to -mx9, default: {SEVEN_ZIP_COMPRESSION_LEVEL})")
    return parser.parse_args()

def main():
    args = parse_arguments()
    compression_level = args.compression_level
    logger = setup_logging(MONTHLY_BACKUP_TYPE, MONTHLY_FREQUENCY, args.debug)

    if not args.archive and not args.par:
        logger.error("Error: At least one of --archive or --par must be specified")
        parser.print_help()
        sys.exit(1)

    if args.par and not args.par.isdigit():
        logger.error("Error: --par requires a date value in YYMMDD format")
        parser.print_help()
        sys.exit(1)

    logger.info("Use --debug option for more detailed logging if needed.")
    logger.info(f"Using 7-Zip compression level: {compression_level}")
    logger.info(f"Default compression level is: {DEFAULT_COMPRESSION_LEVEL}")

    if args.archive:
        archive_task(logger, compression_level)

    if args.par:
        par_task(logger, args.par)

    logger.info("For more detailed logs, use the --debug option when running the script.")
    logger.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        args = parse_arguments()
        logger = setup_logging(MONTHLY_BACKUP_TYPE, MONTHLY_FREQUENCY, args.debug)
        logger.exception("An unexpected error occurred:")
        sys.exit(1)