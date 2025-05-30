# RockPaperScissor/repositories/__init__.py
from .storage import Storage, StorageError
from .sql_storage import SQLStorage  # This will be our DummySQLStorage
# from .combined_storage import CombinedStorage # This will use DummySQLStorage (commented for Hugging Face)
# from .s3_storage import S3Storage # Add later if needed

__all__ = [
    'Storage', 'StorageError',
    'SQLStorage',
    # 'CombinedStorage',  # Commented for Hugging Face
    # 'S3Storage',
]