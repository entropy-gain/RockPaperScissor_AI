# RockPaperScissor/repositories/combined_storage.py
from .storage import Storage, StorageError # Relative import
from .sql_storage import SQLStorage # Relative import
# from .s3_storage import S3Storage # We'll add S3 later
from typing import Dict, Any, Optional

class CombinedStorage(Storage):
    def __init__(self, db_path: str = "data/game_history.db"):
        self.sql_storage = SQLStorage(db_path)
        self._memory_cache = {}  # Simple in-memory cache

    async def initialize(self):
        """Initialize storage components"""
        await self.sql_storage.initialize()

    async def save_game_round(self, game_data: Dict[str, Any]) -> bool:
        """Save game round to both storage and cache"""
        # Save to SQL storage
        success = await self.sql_storage.save_game_round(game_data)
        
        if success:
            # Update memory cache
            session_id = game_data.get('game_id')
            if session_id:
                self._memory_cache[session_id] = game_data
                
        return success

    async def get_game_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get game history from cache or storage"""
        # Try cache first
        if session_id in self._memory_cache:
            return self._memory_cache[session_id]
            
        # If not in cache, get from storage
        history = await self.sql_storage.get_game_history(session_id)
        if history:
            self._memory_cache[session_id] = history
        return history

    async def get_ai_state(self, session_id: str, ai_type: str) -> Optional[Dict[str, Any]]:
        """Get AI state from storage"""
        return await self.sql_storage.get_ai_state(session_id, ai_type)

    async def close(self) -> None:
        """Close storage connections"""
        await self.sql_storage.close()
        self._memory_cache.clear()