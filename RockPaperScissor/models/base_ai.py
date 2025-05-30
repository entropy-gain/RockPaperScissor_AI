# RockPaperScissor/models/base_ai.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional

class BaseAI(ABC):
    def __init__(self):
        self.possible_moves = ["rock", "paper", "scissors"]

    @abstractmethod
    def make_move(self, model_state: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Generate AI's next move.
        Returns:
            str: One of ("rock", "paper", "scissors")
            Dict: Updated model state (can be empty for simple AIs)
        """
        pass