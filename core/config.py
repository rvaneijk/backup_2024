import yaml
from pathlib import Path

# Base directories
BASE_DIR = Path("/mnt/e")
AWS_DIR = BASE_DIR / "mnt/aws.local"
LOG_DIR = BASE_DIR / "BAK"

# Configuration file paths
COMMON_CONFIG = Path("configs/common_config.yaml")
DAILY_CONFIG = Path("configs/daily_config.yaml")
WEEKLY_CONFIG = Path("configs/weekly_config.yaml")
MONTHLY_CONFIG = Path("configs/monthly_config.yaml")

def load_config(config_file):
    """Load and return the configuration from a YAML file."""
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)

# Load configurations
common_config = load_config(COMMON_CONFIG)
daily_config = load_config(DAILY_CONFIG)
weekly_config = load_config(WEEKLY_CONFIG)
monthly_config = load_config(MONTHLY_CONFIG)

# Git directories (shared across all backup types)
GIT_DIRS = common_config['git_dirs']

# Backup types
DAILY_BACKUP_TYPE = daily_config.get('backup_type', 'INCR')
WEEKLY_BACKUP_TYPE = weekly_config.get('backup_type', 'INCR')
MONTHLY_BACKUP_TYPE = monthly_config.get('backup_type', 'FULL')

# Backup frequencies
DAILY_FREQUENCY = 'Daily'
WEEKLY_FREQUENCY = 'Weekly'
MONTHLY_FREQUENCY = 'Monthly'

# Other configurations
ALLOW_SKIP_MONTHLY = monthly_config.get('allow_skip', True)

# Backup folders
DAILY_BACKUP_FOLDERS = daily_config.get('backup_folders', [])
WEEKLY_BACKUP_FOLDERS = weekly_config.get('backup_folders', [])
MONTHLY_BACKUP_FOLDERS = monthly_config.get('backup_folders', [])

# 7-Zip configuration
DEFAULT_COMPRESSION_LEVEL = '-mx5'  # Default balanced compression
SEVEN_ZIP_COMPRESSION_LEVEL = DEFAULT_COMPRESSION_LEVEL
SEVEN_ZIP_ENCRYPTION_METHOD = '-mhe=on'  # Header encryption on
SEVEN_ZIP_SOLID_MODE = '-ms=off'  # Solid mode off for split archives
SEVEN_ZIP_LARGE_FILE_FILTER = '-mf=on'  # Large file filter on

# Environment variable name for backup password
BACKUP_PASSWORD_ENV = 'BACKUP_PASSWORD'