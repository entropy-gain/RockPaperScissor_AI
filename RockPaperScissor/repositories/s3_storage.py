"""S3 storage implementation for game data and LLM interactions."""

import boto3
import json
from typing import Dict, Any, Optional
import uuid
import asyncio
import os
from .storage import Storage, StorageError
from ..utils import setup_logging
from ..config.database import S3_CONFIG

logger = setup_logging()

class S3StorageError(StorageError):
    """Exception for S3 storage specific errors."""
    pass

class S3Storage(Storage):
    """S3 storage management class."""
    
    def __init__(self):
        """Initialize S3 client using configuration from S3_CONFIG."""
        self.s3: Optional[boto3.client] = None
        self.bucket_name = S3_CONFIG["bucket_name"]
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize S3 client asynchronously and verify connection."""
        if self._initialized:
            return
            
        try:
            # Initialize S3 client with credentials from S3_CONFIG
            self.s3 = boto3.client(
                's3',
                region_name=S3_CONFIG["region_name"],
                aws_access_key_id=S3_CONFIG["aws_access_key_id"],
                aws_secret_access_key=S3_CONFIG["aws_secret_access_key"],
                endpoint_url=S3_CONFIG["endpoint_url"]
            )
            
            # Verify connection asynchronously
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.s3.head_bucket(Bucket=self.bucket_name)
            )
            self._initialized = True
            logger.info(f"Successfully connected to S3 bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise S3StorageError(f"Failed to initialize S3 client: {str(e)}")
    
    def _ensure_initialized(self) -> None:
        """Ensure S3 client is initialized before use."""
        if not self._initialized:
            raise S3StorageError("S3 client not initialized. Call initialize() first.")
    
    def _get_game_round_key(self, game_id: str) -> str:
        """Get S3 key for game round data.
        
        Args:
            game_id: Game ID
            
        Returns:
            S3 key for the game round
        """
        return f"game_rounds/{game_id}.json"
    
    def _get_llm_interaction_key(self, game_id: str) -> str:
        """Get S3 key for LLM interaction data.
        
        Args:
            game_id: Game ID
            
        Returns:
            S3 key for the LLM interaction
        """
        random_id = str(uuid.uuid4())
        return f"llm_interactions/{random_id}_{game_id}.json"
    
    async def save_game_round(self, game_data: Dict[str, Any]) -> bool:
        """Save a game round to S3 asynchronously.
        
        Args:
            game_data: Game data to save
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        self._ensure_initialized()
        try:
            key = self._get_game_round_key(game_data['game_id'])
            # Run S3 put_object in a thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=json.dumps(game_data),
                    ContentType='application/json'
                )
            )
            logger.info(f"Successfully saved game round to S3: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to save game round to S3: {str(e)}")
            return False
    
    async def save_llm_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """Save an LLM interaction to S3 asynchronously.
        
        Args:
            interaction_data: LLM interaction data to save
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        self._ensure_initialized()
        try:
            key = self._get_llm_interaction_key(
                interaction_data['game_id']
            )
            # Run S3 put_object in a thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=json.dumps(interaction_data),
                    ContentType='application/json'
                )
            )
            logger.info(f"Successfully saved LLM interaction to S3: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to save LLM interaction to S3: {str(e)}")
            return False
    
    def save_user_state(self, user_id: str, model_name: str, model_state: Dict[str, Any]) -> None:
        """Save user state is not supported in S3 storage.
        
        This method is intentionally not implemented as S3 storage is designed
        for game rounds and LLM interactions only. Use SQLiteStorage for user state management.
        
        Args:
            user_id: User ID
            model_name: Model name
            model_state: Model state data
            
        Raises:
            S3StorageError: Always raised as this operation is not supported
        """
        raise S3StorageError("User state management is not supported in S3 storage. Use SQLiteStorage instead.")
    
    async def close(self) -> None:
        """Close S3 client connection."""
        self._initialized = False
        self.s3 = None 