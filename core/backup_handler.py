import os
import subprocess
import logging
from datetime import datetime
from .config import BASE_DIR, AWS_DIR, BACKUP_PASSWORD_ENV, SEVEN_ZIP_COMPRESSION_LEVEL, SEVEN_ZIP_ENCRYPTION_METHOD

logger = logging.getLogger(__name__)

def backup_folder(dest_dir, source_dir, exclude, backup_type, archive_name):
    NOW = datetime.now().strftime("%y%m%d")
    archive_name = f"{NOW} {backup_type} {archive_name}.7z"
    
    source_path = BASE_DIR / source_dir
    dest_path = AWS_DIR / dest_dir / archive_name

    exclude_option = [f"-xr!{item}" for item in exclude.split()] if exclude else []
    
    try:
        # Backup operation
        subprocess.run([
            "7z", "a", "-t7z", str(dest_path), str(source_path),
            "-mmt=on", SEVEN_ZIP_COMPRESSION_LEVEL, "-m0=lzma2", "-v1g", SEVEN_ZIP_ENCRYPTION_METHOD,
            f"-p{os.environ[BACKUP_PASSWORD_ENV]}", *exclude_option
        ], check=True)
        logger.info(f"Backup successful for {archive_name}")
        
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