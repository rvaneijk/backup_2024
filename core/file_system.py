"""
File system operations for backup processes.

This module provides functions for managing file system operations
related to backup processes, including mounting and unmounting drives,
and ensuring directories exist.
"""

import os
import subprocess
import sys
import logging
from pathlib import Path
from .config import AWS_DIR, BASE_DIR

logger = logging.getLogger(__name__)

def check_mount() -> bool:
    """
    Check if the backup disk is mounted and mount it if necessary.

    Returns:
        bool: True if the backup disk is mounted and accessible, False otherwise.
    """
    if not BASE_DIR.is_mount():
        logger.info("Backup disk is not mounted. Attempting to mount...")
        
        # Try to mount the disk
        result = subprocess.run([
            "sudo", "mount", "-t", "drvfs", "E:", str(BASE_DIR),
            "-o", "metadata,uid=rvaneijk,gid=rvaneijk"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Failed to mount the backup disk: {result.stderr}")
            return False
        else:
            logger.info("Backup disk mounted successfully.")
    else:
        logger.info("Backup disk is already mounted.")
    
    # Check if the AWS_DIR exists
    if not AWS_DIR.exists():
        logger.error(f"Backup directory {AWS_DIR} does not exist. Please check your USB drive.")
        return False
    
    logger.info(f"Backup directory {AWS_DIR} is accessible.")
    return True

def unmount() -> None:
    """
    Unmount the backup disk if it's currently mounted.
    """
    mount_point = Path("/mnt/e")
    
    if mount_point.is_mount():
        logger.info("Unmounting backup disk...")
        result = subprocess.run(["sudo", "umount", str(mount_point)], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Failed to unmount the backup disk: {result.stderr}")
        else:
            logger.info("Backup disk unmounted successfully.")
    else:
        logger.info("Backup disk is not mounted. No need to unmount.")

def ensure_dir_exists(dir_path: str) -> None:
    """
    Ensure that a directory exists, creating it if necessary.

    Args:
        dir_path (str): The path of the directory to check/create.

    Raises:
        SystemExit: If there's a permission error or if the path exists but is not a directory.
    """
    dir_path = Path(dir_path)
    if not dir_path.exists():
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        except PermissionError:
            logger.error(f"Permission denied when trying to create directory: {dir_path}")
            sys.exit(1)
    elif not dir_path.is_dir():
        logger.error(f"Path exists but is not a directory: {dir_path}")
        sys.exit(1)