from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List

class BaseAI(ABC):
    """
    Base class for all AI strategies.
    """
    def __init__(self):
        self.possible_moves = ["rock", "paper", "scissors"]
        
    @abstractmethod
    def make_move(self, model_state: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Generate AI's next move based on game history.
        
        Args:
            history: Game history records, each containing (user_move, ai_type, ai_move)
                    If None, the AI should make a move without historical context
        
        Returns:
            str: One of the valid moves ("rock", "paper", "scissors")
        """
        pass