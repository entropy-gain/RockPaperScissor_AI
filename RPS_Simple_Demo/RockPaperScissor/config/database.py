# Minimal placeholder for database configuration 
# RockPaperScissor/config/database.py
import os
from pathlib import Path

# Base directory for data storage
BASE_DATA_DIR = Path("data")
BASE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# SQLite configuration
SQLITE_CONFIG = {
    "db_path": str(BASE_DATA_DIR / "game_history.db"),
    "timeout": 5.0,
    "check_same_thread": False,
}

# Storage configuration
STORAGE_CONFIG = {
    "primary": "combined",
    "cache_size": 1000,
    "auto_cleanup": True,
    "cleanup_interval": 3600  # 1 hour in seconds
}

# S3 configuration
S3_CONFIG = {
    "bucket_name": os.getenv("AWS_S3_BUCKET_NAME", "your-bucket-name"),
    "region_name": os.getenv("AWS_REGION", "us-east-1"),
    "access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
    "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY")
}