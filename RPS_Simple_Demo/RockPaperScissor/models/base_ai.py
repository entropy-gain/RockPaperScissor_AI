# RockPaperScissor/models/base_ai.py
from typing import Dict, Any, Tuple

class BaseAI:
    possible_moves = ["rock", "paper", "scissors"]
    def make_move(self, model_state: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        """Make a move in the game.
        
        Args:
            model_state: Optional state data for the AI model
            
        Returns:
            Tuple of (move, updated_state) where:
            - move is one of: "rock", "paper", "scissors"
            - updated_state is the new state of the AI model
        """
        raise NotImplementedError