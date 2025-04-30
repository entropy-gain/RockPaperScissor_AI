"""S3 storage implementation for game data and LLM interactions."""

import boto3
import json
from typing import Dict, Any
import uuid
import asyncio
from .storage import Storage, StorageError

class S3StorageError(StorageError):
    """Exception for S3 storage specific errors."""
    pass

class S3Storage(Storage):
    """S3 storage management class."""
    
    def __init__(self, bucket_name: str, region_name: str = "us-east-1"):
        """Initialize S3 client.
        
        Args:
            bucket_name: Name of the S3 bucket
            region_name: AWS region name
        """
        try:
            self.s3 = boto3.client('s3', region_name=region_name)
            self.bucket_name = bucket_name
        except Exception as e:
            raise S3StorageError(f"Failed to initialize S3 client: {str(e)}")
    
    def _get_game_round_key(self, game_id: str) -> str:
        """Get S3 key for game round data.
        
        Args:
            game_id: Game ID
            
        Returns:
            S3 key for the game round
        """
        return f"game_rounds/{game_id}.json"
    
    def _get_llm_interaction_key(self, session_id: str, game_id: str) -> str:
        """Get S3 key for LLM interaction data.
        
        Args:
            session_id: Session ID
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
            return True
        except Exception as e:
            logger.error(f"Failed to save LLM interaction to S3: {str(e)}")
            return False
    
    def save_user_state(self, user_id: str, model_name: str, model_state: Dict[str, Any]) -> None:
        """Not implemented for S3 storage."""
        raise NotImplementedError("S3 storage does not support saving user states")
    
    async def close(self) -> None:
        """Close S3 client connection."""
        # S3 client doesn't need explicit closing
        pass 