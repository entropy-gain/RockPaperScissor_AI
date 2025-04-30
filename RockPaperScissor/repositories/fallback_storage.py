"""Fallback storage implementation that tries S3 first, then falls back to SQL."""

from typing import Dict, Any
from .storage import Storage, StorageError
from .s3_storage import S3Storage, S3StorageError
from .sql_storage import SQLStorage

class FallbackStorageError(StorageError):
    """Exception for fallback storage specific errors."""
    pass

class FallbackStorage(Storage):
    """Storage implementation that falls back to SQL when S3 fails."""
    
    def __init__(self, s3_bucket: str, sql_db_path: str = "data/game_data.db"):
        """Initialize storage with fallback mechanism.
        
        Args:
            s3_bucket: S3 bucket name
            sql_db_path: Path to SQLite database
        """
        self.primary = S3Storage(bucket_name=s3_bucket)
        self.fallback = SQLStorage(db_path=sql_db_path)
    
    async def save_game_round(self, game_data: Dict[str, Any]) -> bool:
        """Save game round with fallback to SQL if S3 fails."""
        try:
            return await self.primary.save_game_round(game_data)
        except S3StorageError:
            # Fall back to SQL storage
            return await self.fallback.save_game_round(game_data)
    
    async def save_llm_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """Save LLM interaction with fallback to SQL if S3 fails."""
        try:
            return await self.primary.save_llm_interaction(interaction_data)
        except S3StorageError:
            # Fall back to SQL storage
            return await self.fallback.save_llm_interaction(interaction_data)
    
    async def close(self) -> None:
        """Close both storage connections."""
        await self.primary.close()
        await self.fallback.close()
    
    @property
    def sql_storage(self) -> SQLStorage:
        """Get the SQL storage instance for direct access to user states."""
        return self.fallback 