# RockPaperScissor/repositories/storage.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class StorageError(Exception):
    pass

class Storage(ABC):
    async def initialize(self): # Add initialize method
        pass

    @abstractmethod
    async def save_game_round(self, game_data: Dict[str, Any]) -> bool:
        pass

    # We don't need these for the minimal version with GameService not using user states yet
    # def get_user_state(self, user_id: str) -> Optional[Dict[str, Any]]:
    #     return None
    # def save_user_state(self, user_id: str, model_name: str, model_state: Dict[str, Any]) -> None:
    #     pass

    async def close(self) -> None:
        pass