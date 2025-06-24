# RockPaperScissor/repositories/__init__.py
from .storage import Storage, StorageError
from .sql_storage import SQLStorage  # This will be our DummySQLStorage
from .combined_storage import CombinedStorage # This will use DummySQLStorage
from .s3_storage import S3Storage # Add later if needed

__all__ = [
    'Storage', 'StorageError',
    'SQLStorage',
    'CombinedStorage',  # Uncommented for S3 testing
    'S3Storage',
]