"""
Logging functionality for backup jobs.

This module provides a custom JobLogger class for handling logging operations
specific to backup jobs. It also includes utility functions for logging and
directory size calculation.
"""

import logging
import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
from .config import LOG_DIR, AWS_DIR

def get_directory_size(path: str) -> int:
    """
    Calculate the total size of a directory.

    Args:
        path (str): The path to the directory.

    Returns:
        int: The total size of the directory in bytes.
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

class JobLogger:
    """
    Custom logger for backup jobs.

    This class provides methods for logging various events and information
    related to backup jobs.
    """

    def __init__(self, backup_type: str, backup_frequency: str, debug_mode: bool = False):
        """
        Initialize the JobLogger.

        Args:
            backup_type (str): The type of backup (e.g., 'full', 'incremental').
            backup_frequency (str): The frequency of the backup (e.g., 'daily', 'weekly').
            debug_mode (bool, optional): Whether to enable debug logging. Defaults to False.
        """
        self.backup_type = backup_type
        self.backup_frequency = backup_frequency
        self.start_time = datetime.now()
        self.debug_mode = debug_mode
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """
        Set up the logging configuration.

        Returns:
            logging.Logger: Configured logger object.
        """
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / f"{self.start_time:%y%m%d}_{self.backup_type}_{self.backup_frequency}.log"
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%y-%m-%d %H:%M:%S')

        file_handler = logging.FileHandler(log_file, mode='a', delay=False)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        job_name = f"{self.start_time:%Y%m%d-%w}. {self.backup_frequency} - {self.backup_type}"
        
        if log_file.stat().st_size == 0:
           logger.info(f"========================= Job Start: {job_name} ==========================")
           logger.info(f"Logging started ({log_file})")
           logger.info(f"========================================================================================")
        else:
            logger.info(f"========================= Job Start: {job_name} ==========================")
            logger.info(f"Appending to existing log file ({log_file})")
            logger.info(f"========================================================================================")
        
        return logger

    def debug(self, message):
        if self.debug_mode:
            self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def exception(self, message):
        self.logger.exception(message)

    def log_backup_start(self, source_folder):
        self.logger.info(f"Backing up {source_folder}...")

    def log_backup_success(self, archive_name):
        self.logger.info(f"Backup successful: {archive_name}")

    def log_backup_test(self, archive_name):
        self.logger.info(f"Backup test successful: {archive_name}")

    def log_backup_failure(self, archive_name, error):
        self.logger.error(f"Backup failed: {archive_name}")
        self.logger.error(f"Error: {error}")

    def log_backup_stats(self, archive_name, size, duration):
        self.logger.info(f"Backup stats for {archive_name}:")
        self.logger.info(f"  Size: {size:.2f} GB")
        self.logger.info(f"  Duration: {duration}")

    def generate_archive_name(self, base_name):
        return f"{datetime.now():%y%m%d} {self.backup_type} {base_name}.7z"

    def log_git_status(self, folder):
        try:
            os.chdir(folder)
            status_output = subprocess.check_output(['git', 'status', '--porcelain']).decode('utf-8').strip()
            
            if status_output:
                self.logger.info(f"Changes detected in {folder}:")
                for line in status_output.split('\n'):
                    status, filename = line[:2], line[3:]
                    if status == '??':
                        self.logger.info(f"  New file: {filename}")
                    elif status == ' M':
                        self.logger.info(f"  Modified: {filename}")
                    elif status == ' D':
                        self.logger.info(f"  Deleted: {filename}")
                    else:
                        self.logger.info(f"  {status} {filename}")
                
                subprocess.run(['git', 'add', '.'], check=True)
                commit_message = f"{datetime.now():%y%m%d %H:%M}"
                subprocess.run(['git', 'commit', '-m', commit_message], check=True)
                self.logger.info(f"Changes committed in {folder}")
                
                last_commit = subprocess.check_output(['git', 'log', '-1', '--oneline']).decode('utf-8').strip()
                self.logger.info(f"Last commit: {last_commit}")
            else:
                self.logger.info(f"No changes to commit in {folder}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git operation failed in {folder}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error processing {folder}: {str(e)}")

    def close(self):
        end_time = datetime.now()
        duration = end_time - self.start_time
        job_name = f"{self.start_time:%Y%m%d-%w}. {self.backup_frequency} - {self.backup_type}"
        
        backup_path = "/mnt/e/mnt/aws.local"
        backup_size = get_directory_size(backup_path)
        backup_size_gb = backup_size / (1024 * 1024 * 1024)  # Convert to GB
        
        self.logger.info(f"========================== Job End: {job_name} ===========================")
        self.logger.info(f"{self.start_time.strftime('%d-%m-%Y %H:%M:%S')}  Job started")
        self.logger.info(f"{end_time.strftime('%d-%m-%Y %H:%M:%S')}  Job completed")
        self.logger.info(f"Duration: {duration}")
        self.logger.info("")  # Add an empty line
        self.logger.info(f"Backup size (/mnt/e/mnt/aws.local): {backup_size_gb:.2f} GB")
        
        if backup_size_gb >= 900:
            self.logger.warning("")  # Add an empty line
            self.logger.warning("")  # Add an empty line
            self.logger.warning("Consider purging files")
            self.logger.warning("")  # Add an empty line
            self.logger.warning("")  # Add an empty line
        
        self.logger.info(f"========================================================================================")

def setup_logging(backup_type: str, backup_frequency: str, debug_mode: bool = False) -> JobLogger:
    """
    Set up and return a JobLogger instance.

    Args:
        backup_type (str): The type of backup.
        backup_frequency (str): The frequency of the backup.
        debug_mode (bool, optional): Whether to enable debug logging. Defaults to False.

    Returns:
        JobLogger: An instance of the JobLogger class.
    """
    return JobLogger(backup_type, backup_frequency, debug_mode)