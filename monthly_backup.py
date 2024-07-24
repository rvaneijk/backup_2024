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

Usage:
    For archive task only:
    $ python monthly_backup.py --archive [--debug]

    For PAR file creation task only:
    $ python monthly_backup.py --par YYMMDD [--debug]

    where YYMMDD is the date of the backup in YYMMDD format.

Environment Variables:
    BACKUP_PASSWORD_ENV: Must be set for the archive task (contains the backup password)

Dependencies:
    - core package (config, logger, file_system, backup_handler, utils, git_handler)
    - Standard libraries: os, sys, subprocess, argparse, datetime, yaml
    - External: par2 command-line tool (for PAR task)
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime
import yaml
from typing import List, Dict, Set

from core.config import (
    AWS_DIR, MONTHLY_BACKUP_TYPE, MONTHLY_FREQUENCY,
    MONTHLY_BACKUP_FOLDERS, BACKUP_PASSWORD_ENV, ALLOW_SKIP_MONTHLY,
    MONTHLY_CONFIG, GIT_DIRS
)
from core.logger import setup_logging
from core.file_system import check_mount, ensure_dir_exists
from core.backup_handler import backup_folder
from core.utils import timer
from core.git_handler import git_operations

def run_command(command: str) -> bool:
    """
    Execute a shell command and return its success status.

    Args:
        command (str): The command to execute.

    Returns:
        bool: True if the command was successful, False otherwise.
    """
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: Command failed with error: {result.stderr}")
    return result.returncode == 0

def process_directory(base_dir: str, archive_name: str, incr: str, logger) -> None:
    """
    Process a directory for PAR file creation.

    Args:
        base_dir (str): The base directory to process.
        archive_name (str): The name of the archive.
        incr (str): The increment value.
        logger: The logger object.
    """
    os.chdir(base_dir)
    logger.info(f"Processing {base_dir}")
    
    subdirs = sorted([d for d in os.listdir() if os.path.isdir(d) and d[0].isdigit()])
    
    for subdir in subdirs:
        os.chdir(subdir)
        logger.info(f"  Processing subdirectory: {subdir}")
        
        # Move relevant files into the subdirectory
        for file in os.listdir('..'):
            if file.startswith(f"{incr} FULL {archive_name}.7z."):
                os.rename(os.path.join('..', file), file)
        
        # Create par2 files
        par2_create = f"par2 create -c625 {incr}\\ FULL\\ {archive_name}.7z.*"
        logger.info(f"Executing PAR2 command: {par2_create}")
        result = subprocess.run(par2_create, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"  par2 create failed for {subdir}")
            logger.debug(f"PAR2 create stdout: {result.stdout}")
            logger.debug(f"PAR2 create stderr: {result.stderr}")
        else:
            logger.info(f"  par2 create successful for {subdir}")
        
        os.chdir('..')
    
    # Check for any remaining files
    remaining_files = [f for f in os.listdir() if f.startswith(f"{incr} FULL {archive_name}.7z.")]
    if remaining_files:
        logger.warning(f"The following files were not processed: {', '.join(remaining_files)}")
    else:
        logger.info("All files processed successfully.")

def get_items_to_skip(items: List[Dict], skip_prompt: str) -> Set[int]:
    """
    Prompt the user to select items to skip during processing.

    Args:
        items (List[Dict]): List of items to potentially skip.
        skip_prompt (str): The prompt to display to the user.

    Returns:
        Set[int]: Set of item numbers to skip.
    """
    print(skip_prompt)
    for i, item in enumerate(items, 1):
        print(f"{i}. {item['archive_name']}")
    skip_input = input("Enter numbers to skip (or press Enter to process all): ")
    skip_numbers = [int(num) for num in skip_input.split() if num.isdigit()]
    return set(skip_numbers)

def load_config(config_file: str) -> Dict:
    """
    Load configuration from a YAML file.

    Args:
        config_file (str): Path to the YAML config file.

    Returns:
        Dict: Loaded configuration.

    Raises:
        SystemExit: If there's an error parsing the config file or if it's not found.
    """
    try:
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as e:
        print(f"Error parsing config file: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Config file not found: {config_file}")
        sys.exit(1)

def archive_task(logger) -> None:
    """
    Perform the archive task (monthly backup).

    Args:
        logger: The logger object.
    """
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
            archive_name=folder['archive_name']
        ):
            logger.error(f"Backup failed for {folder['archive_name']}. Exiting.")
            sys.exit(1)
    
    end_time = timer(start_time)
    logger.info(f"Monthly backup process completed. Total duration: {end_time}")

def par_task(logger, incr: str) -> None:
    """
    Perform the PAR task (create and verify PAR2 files).

    Args:
        logger: The logger object.
        incr (str): The increment value.
    """
    config = load_config(MONTHLY_CONFIG)
    archives = config['backup_folders']
    
    archives_to_skip = get_items_to_skip(archives, "Select archives to skip (enter the number, separated by spaces):")
    
    start_time = datetime.now()
    logger.info(f"Starting par file creation process... ({start_time.strftime('%y%m%d %H:%M')})")
    
    for i, archive in enumerate(archives, 1):
        if i in archives_to_skip:
            logger.info(f"Skipping {archive['archive_name']}...")
            continue
        
        full_path = AWS_DIR / archive['dest']
        if os.path.exists(full_path):
            process_directory(full_path, archive['archive_name'], incr, logger)
        else:
            logger.warning(f"Directory {full_path} does not exist. Skipping.")
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Par file creation completed! (Duration: {duration})")

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Monthly backup and optional PAR file creation script")
    parser.add_argument("--archive", action="store_true", help="Run the archive task")
    parser.add_argument("--par", help="Run the PAR file creation task. Requires a date value in YYMMDD format.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()

def main() -> None:
    """
    Main function to parse command-line arguments and execute the appropriate task(s).
    """
    args = parse_arguments()
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

    if args.archive:
        archive_task(logger)

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