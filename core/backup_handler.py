"""
Backup handling functionality.

This module provides functions for performing backups using 7-Zip.
"""

import os
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from .config import BASE_DIR, AWS_DIR, BACKUP_PASSWORD_ENV, SEVEN_ZIP_COMPRESSION_LEVEL, SEVEN_ZIP_ENCRYPTION_METHOD

logger = logging.getLogger(__name__)

def backup_folder(dest_dir: str, source_dir: str, exclude: Optional[str], backup_type: str, archive_name: str) -> bool:
    """
    Perform a backup of a folder using 7-Zip.

    Args:
        dest_dir (str): The destination directory for the backup.
        source_dir (str): The source directory to be backed up.
        exclude (Optional[str]): A string of paths to exclude from the backup, separated by spaces.
        backup_type (str): The type of backup (e.g., 'full', 'incremental').
        archive_name (str): The name of the archive to be created.

    Returns:
        bool: True if the backup was successful, False otherwise.
    """
    NOW = datetime.now().strftime("%y%m%d")
    archive_name = f"{NOW} {backup_type} {archive_name}.7z"
    
    source_path = BASE_DIR / source_dir
    dest_path = AWS_DIR / dest_dir / archive_name

    exclude_option: List[str] = [f"-xr!{item}" for item in exclude.split()] if exclude else []
    
    try:
        # Backup operation
        backup_result = subprocess.run([
            "7z", "a", "-t7z", str(dest_path), str(source_path),
            "-mmt=on", SEVEN_ZIP_COMPRESSION_LEVEL, "-m0=lzma2", "-v1g", SEVEN_ZIP_ENCRYPTION_METHOD,
            f"-p{os.environ[BACKUP_PASSWORD_ENV]}", *exclude_option
        ], check=True)
        logger.info(f"Backup successful for {archive_name}")
        logger.debug(f"Backup output: {backup_result.stdout}")
        
        # Test operation
        logger.info(f"Testing {archive_name}...")
        test_result = subprocess.run([
            "7z", "t", f"{dest_path}.001", f"-p{os.environ[BACKUP_PASSWORD_ENV]}"
        ], capture_output=True, text=True, check=True)
        logger.info(f"Test successful for {archive_name}")
        logger.debug(f"Test output: {test_result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup operation failed for {archive_name}: {e}")
        return False
    except KeyError:
        logger.error(f"Environment variable {BACKUP_PASSWORD_ENV} is not set")
        return False
    return True