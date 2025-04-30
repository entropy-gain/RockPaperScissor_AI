"""Database configuration settings."""

import os
from pathlib import Path

# Base directory for data storage
BASE_DATA_DIR = Path("data")

# Ensure data directory exists
BASE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# SQLite database configuration
SQLITE_CONFIG = {
    "db_path": str(BASE_DATA_DIR / "game_data.db"),
    "timeout": 30.0,  # Wait up to 30 seconds for locks
    "check_same_thread": False,  # Allow multi-threaded access
}

# S3 configuration
S3_CONFIG = {
    "bucket_name": os.getenv("S3_BUCKET_NAME", "your-bucket-name"),
    "region_name": os.getenv("AWS_REGION", "us-east-1"),
}

# Storage configuration
STORAGE_CONFIG = {
    "primary": "s3",  # Primary storage type: "s3" or "sql"
    "fallback": "sql",  # Fallback storage type
    "batch_size": 100,  # Number of records to batch
    "batch_timeout_sec": 300,  # Maximum time to wait before flushing batch
} 