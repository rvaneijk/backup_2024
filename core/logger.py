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
        # ... (rest of the method implementation)

    # ... (rest of the class methods)

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