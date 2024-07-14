import os
import subprocess
import logging
from datetime import datetime
from .config import BASE_DIR, AWS_DIR

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
            "-mmt=on", "-mx3", "-m0=lzma2", "-v1g", "-mhe=on",
            f"-p{os.environ['BACKUP_PASSWORD']}", *exclude_option
        ], check=True)
        logger.info(f"Backup successful for {dest_dir}")
        
        # Test operation
        test_result = subprocess.run([
            "7z", "t", f"{dest_path}.001", f"-p{os.environ['BACKUP_PASSWORD']}"
        ], capture_output=True, text=True, check=True)
        logger.info(f"Backup test successful for {dest_dir}")
        logger.debug(f"Test output: {test_result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup operation failed for {dest_dir}: {e}")
        return False
    return True