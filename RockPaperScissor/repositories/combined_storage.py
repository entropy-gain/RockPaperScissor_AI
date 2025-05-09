"""Combined storage implementation that uses both S3 and SQL storage."""

from typing import Dict, Any, Optional, List
from .storage import Storage, StorageError
from .s3_storage import S3Storage, S3StorageError
from .sql_storage import SQLStorage, SQLStorageError
from ..utils import setup_logging
import asyncio

logger = setup_logging()

class CombinedStorageError(StorageError):
    """Exception for combined storage specific errors."""
    pass

class CombinedStorage(Storage):
    """Storage implementation that uses both S3 and SQL storage."""
    
    def __init__(self):
        """Initialize both S3 and SQL storage."""
        try:
            self.s3_storage = S3Storage()
            self.sql_storage = SQLStorage()
            self.s3_available = True  # Flag to track S3 availability
            logger.info("Successfully initialized combined storage")
        except Exception as e:
            logger.error(f"Failed to initialize combined storage: {str(e)}")
            raise CombinedStorageError(f"Failed to initialize combined storage: {str(e)}")
    
    async def initialize(self):
        """Initialize SQL storage."""
        await self.sql_storage.initialize()
    
    async def save_game_round(self, game_data: Dict[str, Any]) -> bool:
        """Save game round to storage, with dynamic primary storage selection."""
        try:
            if self.s3_available:
                # Try S3 first
                try:
                    success = await self.s3_storage.save_game_round(game_data)
                    if success:
                        return True
                except Exception as e:
                    logger.error(f"S3 storage error: {str(e)}")
                    self.s3_available = False
                    logger.info("Switching to SQL as primary storage")
            
            # Use SQL storage (either as fallback or primary)
            success = await self.sql_storage.save_game_round(game_data)
            if not success:
                logger.error("Failed to save game round to SQL")
            return success
            
        except Exception as e:
            logger.error(f"Failed to save game round: {str(e)}")
            return False
    
    async def save_llm_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """Save LLM interaction to storage, with dynamic primary storage selection."""
        try:
            if self.s3_available:
                # Try S3 first
                try:
                    success = await self.s3_storage.save_llm_interaction(interaction_data)
                    if success:
                        return True
                except Exception as e:
                    logger.error(f"S3 storage error: {str(e)}")
                    self.s3_available = False
                    logger.info("Switching to SQL as primary storage")
            
            # Use SQL storage (either as fallback or primary)
            success = await self.sql_storage.save_llm_interaction(interaction_data)
            if not success:
                logger.error("Failed to save LLM interaction to SQL")
            return success
            
        except Exception as e:
            logger.error(f"Failed to save LLM interaction: {str(e)}")
            return False
    
    def get_user_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user state from SQL storage."""
        return self.sql_storage.get_user_state(user_id)
    
    def save_user_state(self, user_id: str, model_name: str, model_state: Dict[str, Any]) -> None:
        """Save user state to SQL storage."""
        self.sql_storage.save_user_state(user_id, model_name, model_state)
    
    async def close(self) -> None:
        """Close both storage connections."""
        try:
            await self.sql_storage.close()
            # S3 doesn't need explicit closing
            logger.info("Successfully closed combined storage")
        except Exception as e:
            logger.error(f"Error closing combined storage: {str(e)}")
            raise CombinedStorageError(f"Failed to close combined storage: {str(e)}")
    
    async def save_batch_game_rounds(self, game_data_list: List[Dict[str, Any]]) -> bool:
        """Save multiple game rounds to storage in a batch, with dynamic primary storage selection.
        
        Args:
            game_data_list: List of game data to save
            
        Returns:
            bool: True if all saves were successful, False otherwise
        """
        try:
            if self.s3_available:
                # Try S3 first
                try:
                    # For S3, we need to save each record individually since it's object storage
                    tasks = [self.s3_storage.save_game_round(data) for data in game_data_list]
                    results = await asyncio.gather(*tasks)
                    if all(results):
                        return True
                except Exception as e:
                    logger.error(f"S3 storage error: {str(e)}")
                    self.s3_available = False
                    logger.info("Switching to SQL as primary storage")
            
            # Use SQL storage (either as fallback or primary)
            success = await self.sql_storage.save_batch_game_rounds(game_data_list)
            if not success:
                logger.error("Failed to save game rounds to SQL")
            return success
            
        except Exception as e:
            logger.error(f"Failed to save game rounds: {str(e)}")
            return False
    
    async def save_batch_llm_interactions(self, interaction_data_list: List[Dict[str, Any]]) -> bool:
        """Save multiple LLM interactions to storage in a batch, with dynamic primary storage selection.
        
        Args:
            interaction_data_list: List of LLM interaction data to save
            
        Returns:
            bool: True if all saves were successful, False otherwise
        """
        try:
            if self.s3_available:
                # Try S3 first
                try:
                    # For S3, we need to save each record individually since it's object storage
                    tasks = [self.s3_storage.save_llm_interaction(data) for data in interaction_data_list]
                    results = await asyncio.gather(*tasks)
                    if all(results):
                        return True
                except Exception as e:
                    logger.error(f"S3 storage error: {str(e)}")
                    self.s3_available = False
                    logger.info("Switching to SQL as primary storage")
            
            # Use SQL storage (either as fallback or primary)
            success = await self.sql_storage.save_batch_llm_interactions(interaction_data_list)
            if not success:
                logger.error("Failed to save LLM interactions to SQL")
            return success
            
        except Exception as e:
            logger.error(f"Failed to save LLM interactions: {str(e)}")
            return False 