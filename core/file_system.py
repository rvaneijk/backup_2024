import os
import subprocess
import sys
import logging
from pathlib import Path
from .config import AWS_DIR, BASE_DIR

logger = logging.getLogger(__name__)

def check_mount():
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

def unmount():
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

def ensure_dir_exists(dir_path):
    """Ensure that a directory exists, creating it if necessary."""
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