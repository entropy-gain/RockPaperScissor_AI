"""Base storage interface for different storage implementations."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class StorageError(Exception):
    """Base exception for storage errors."""
    pass

class Storage(ABC):
    """Abstract base class for storage implementations."""
    
    @abstractmethod
    async def save_game_round(self, game_data: Dict[str, Any]) -> bool:
        """Save a game round.
        
        Args:
            game_data: Game data to save
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def save_llm_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """Save an LLM interaction.
        
        Args:
            interaction_data: LLM interaction data to save
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the storage connection."""
        pass 