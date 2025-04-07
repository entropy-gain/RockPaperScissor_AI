# RockPaperScissor/models/random_ai.py
import random
from RockPaperScissor.models.base_ai import BaseAI

class RandomAI(BaseAI):
    """
    AI that makes random moves
    """
    def make_move(self, model_state=None):
        """
        Makes a random move
        
        Args:
            previous_moves (list, optional): Not used in this strategy
            
        Returns:
            str: A random choice from ["rock", "paper", "scissors"]
        """
        if not model_state:
            return random.choice(self.possible_moves), {"player_last_move" : None}
        else:
            # Choose counter move
            if model_state["player_last_move"] == "rock":
                ai_move = "paper"
            elif model_state["player_last_move"] == "paper":
                ai_move = "scissors"
            else:  # scissors
                ai_move = "rock"
            return ai_move, {"player_last_move" : None}