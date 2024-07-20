import logging
import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path
from .config import LOG_DIR, AWS_DIR

def get_directory_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

class JobLogger:
    def __init__(self, backup_type, backup_frequency):
        self.backup_type = backup_type
        self.backup_frequency = backup_frequency
        self.start_time = datetime.now()
        self.logger = self._setup_logging()

    def _setup_logging(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / f"{self.start_time:%y%m%d}_{self.backup_type}_{self.backup_frequency}.log"
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%y-%m-%d %H:%M:%S')

        file_handler = logging.FileHandler(log_file, mode='a', delay=False)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[file_handler, console_handler]
        )
        
        logger = logging.getLogger(__name__)
        
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

def setup_logging(backup_type, backup_frequency):
    return JobLogger(backup_type, backup_frequency)