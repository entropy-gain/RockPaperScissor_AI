import random
from collections import defaultdict
from typing import Dict, Any, Optional, Tuple

from .base_ai import BaseAI

class MarkovAI(BaseAI):
    """
    An AI that uses Markov chains to predict player moves.
    """
    
    def make_move(self, model_state: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a move based on Markov chain prediction of player's next move.
        
        Args:
            model_state: Dictionary containing:
                - transition_matrix: Markov transition probabilities
                - player_last_move: The player's most recent move
                
        Returns:
            Tuple containing:
            - str: Selected move
            - Dict: Updated model state
        """
        # Initialize state if not provided
        if model_state is None:
            model_state = {
                "transition_matrix": {
                    "rock": {"rock": 0, "paper": 0, "scissors": 0},
                    "paper": {"rock": 0, "paper": 0, "scissors": 0},
                    "scissors": {"rock": 0, "paper": 0, "scissors": 0}
                },
                "player_last_move": None,
                "player_second_last_move": None
            }
        
        transition_matrix = model_state.get("transition_matrix", {
            "rock": {"rock": 0, "paper": 0, "scissors": 0},
            "paper": {"rock": 0, "paper": 0, "scissors": 0},
            "scissors": {"rock": 0, "paper": 0, "scissors": 0}
        })
        player_last_move = model_state.get("player_last_move", None)
        player_second_last_move = model_state.get("player_second_last_move", None)
        
        # Update transition matrix if we have two consecutive moves
        if player_second_last_move is not None and player_last_move is not None:
            transition_matrix[player_second_last_move][player_last_move] += 1
        
        # Predict next move based on Markov chain
        predicted_move = None
        if player_last_move is not None:
            # Get transition probabilities from current state
            transitions = transition_matrix[player_last_move]
            total = sum(transitions.values())
            
            if total > 0:
                # Predict based on highest probability
                predicted_move = max(transitions, key=transitions.get)
            else:
                # No transitions recorded yet, choose randomly
                predicted_move = random.choice(self.possible_moves)
        else:
            predicted_move = random.choice(self.possible_moves)
        
        # Choose counter move
        if predicted_move == "rock":
            ai_move = "paper"
        elif predicted_move == "paper":
            ai_move = "scissors"
        else:  # scissors
            ai_move = "rock"
        
        # Return move and updated state
        return ai_move, {
            "transition_matrix": transition_matrix,
            "player_last_move": None,
            "player_second_last_move": player_last_move
        }