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
    "primary": "sql",
    "cache_size": 1000,
    "auto_cleanup": True,
    "cleanup_interval": 3600  # 1 hour in seconds
}

# Minimal S3 and Storage config, won't be used actively in this minimal version
S3_CONFIG = { "bucket_name": "your-bucket-name" }