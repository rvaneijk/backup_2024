import logging
import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path
from .config import LOG_DIR

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
            level=logging.INFO,
            handlers=[file_handler, console_handler]
        )
        
        logger = logging.getLogger(__name__)
        
        if log_file.stat().st_size == 0:
            logger.info(f"Logging started ({log_file})")
        else:
            logger.info(f"Appending to existing log file ({log_file})")
        
        job_name = f"{self.start_time:%Y%m%d-%w}. {self.backup_frequency} - {self.backup_type}"
        logger.info(f"================================ Job Start: {job_name} =================================")
        
        return logger

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def log_git_status(self, folder):
        try:
            # Change to the folder directory
            os.chdir(folder)
            
            # Get git status
            status_output = subprocess.check_output(['git', 'status', '--porcelain']).decode('utf-8').strip()
            
            if status_output:
                # There are changes, log the detailed status
                self.logger.info(f"Changes detected in {folder}:")
                
                # Process each line of the status output
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
                
                # Add and commit changes
                subprocess.run(['git', 'add', '.'], check=True)
                commit_message = f"{datetime.now():%y%m%d %H:%M}"
                subprocess.run(['git', 'commit', '-m', commit_message], check=True)
                self.logger.info(f"Changes committed in {folder}")
                
                # Log the last commit
                last_commit = subprocess.check_output(['git', 'log', '-1', '--oneline']).decode('utf-8').strip()
                self.logger.info(f"Last commit: {last_commit}")
            else:
                # No changes
                self.logger.info(f"No changes to commit in {folder}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git operation failed in {folder}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error processing {folder}: {str(e)}")

    def close(self):
        end_time = datetime.now()
        duration = end_time - self.start_time
        job_name = f"{self.start_time:%Y%m%d-%w}. {self.backup_frequency} - {self.backup_type}"
        
        # Get the size of the backup directory
        backup_path = "/mnt/e/mnt/aws.local"
        backup_size = get_directory_size(backup_path)
        backup_size_gb = backup_size / (1024 * 1024 * 1024)  # Convert to GB
        
        self.logger.info(f"================================= Job End: {job_name} ==================================")
        self.logger.info(f"{job_name}")
        self.logger.info(f"{self.start_time.strftime('%d-%m-%Y %H:%M:%S')}  Job {self.backup_type} {self.backup_frequency} started")
        self.logger.info(f"{end_time.strftime('%d-%m-%Y %H:%M:%S')}  Job {self.backup_type} {self.backup_frequency} ended")
        self.logger.info(f"Duration: {duration}")
        self.logger.info(f"Backup size (/mnt/e/mnt/aws.local): {backup_size_gb:.2f} GB")
        
        # Add warning if backup size is 900 GB or larger
        if backup_size_gb >= 900:
            self.logger.warning("WARNING: consider purging files")
        
        self.logger.info("")  # Add an empty line

def setup_logging(backup_type, backup_frequency):
    return JobLogger(backup_type, backup_frequency)