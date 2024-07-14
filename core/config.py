import yaml
from pathlib import Path

BASE_DIR = Path("/mnt/e")
AWS_DIR = BASE_DIR / "mnt/aws.local"
LOG_DIR = Path.home() / "backup_logs"

def load_config(config_file):
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)