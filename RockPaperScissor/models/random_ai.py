# RockPaperScissor/models/random_ai.py
import random
from typing import Dict, Any, Tuple, Optional
from .base_ai import BaseAI # Assuming base_ai.py is in the same directory

class RandomAI(BaseAI):
    def make_move(self, model_state: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """Makes a random move."""
        # model_state is ignored by RandomAI
        # Returns the chosen move and an empty dictionary for the (unchanged) state
        return random.choice(self.possible_moves), {}