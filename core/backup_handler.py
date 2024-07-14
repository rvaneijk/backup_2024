import os
import subprocess
import logging
from datetime import datetime
from .config import BASE_DIR, AWS_DIR

logger = logging.getLogger(__name__)

def backup_folder(dest_dir, source_dir, exclude, backup_type="INCR", archive_name=None):
    NOW = datetime.now().strftime("%y%m%d")
    if archive_name:
        archive_name = f"{NOW} {archive_name}.7z"
    else:
        archive_name = f"{NOW} {backup_type} {dest_dir.split('/')[-1]}.7z"
    source_path = BASE_DIR / source_dir
    dest_path = AWS_DIR / dest_dir / archive_name

    exclude_option = [f"-xr!{item}" for item in exclude.split()] if exclude else []
    
    try:
        subprocess.run([
            "7z", "a", "-t7z", str(dest_path), str(source_path),
            "-mmt=on", "-mx3", "-m0=lzma2", "-v1g", "-mhe=on",
            f"-p{os.environ['BACKUP_PASSWORD']}", *exclude_option
        ], check=True)
        
        subprocess.run([
            "7z", "t", f"{dest_path}.001", f"-p{os.environ['BACKUP_PASSWORD']}"
        ], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup operation failed for {dest_dir}: {e}")
        return False
    return True