import random
from collections import defaultdict
from typing import Dict, Any, Optional, Tuple, List

from .base_ai import BaseAI

class PatternAI(BaseAI):
    """
    An AI that recognizes patterns in player moves.
    """

    def make_move(self, model_state: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a move based on pattern recognition of player's previous moves.

        Args:
            model_state: Dictionary containing:
                - player_moves: List of previous player moves
                - pattern_dict: Dictionary mapping move sequences to next moves
                - sequence_length: Length of sequences to track

        Returns:
            Tuple containing:
            - str: Selected move
            - Dict: Updated model state
        """
        # Initialize state if not provided
        if model_state is None:
            model_state = {
                "player_last_move": None,
                "player_moves": [],
                "pattern_dict": defaultdict(list),
                "sequence_length": 3  # Default pattern length to recognize
            }
        
        player_last_move = model_state.get("player_last_move", None)
        player_moves = model_state.get("player_moves", [])
        pattern_dict = model_state.get("pattern_dict", defaultdict(list))
        sequence_length = model_state.get("sequence_length", 3)

        if player_last_move:
            player_moves.append(player_last_move)
            
        # If we don't have enough history, choose randomly
        if len(player_moves) < sequence_length:
            return random.choice(self.possible_moves), model_state

        # Update pattern dictionary with new patterns (if there's a new player move)
        for i in range(len(player_moves) - sequence_length):
            seq = tuple(player_moves[i:i+sequence_length])
            if i + sequence_length < len(player_moves):
                next_move = player_moves[i+sequence_length]
                pattern_dict[seq].append(next_move)

        # Get the most recent sequence of moves
        recent_sequence = tuple(player_moves[-sequence_length:])

        # Predict next player move based on pattern matching
        predicted_move = None
        if recent_sequence in pattern_dict and pattern_dict[recent_sequence]:
            # Count frequency of moves following this sequence
            move_counts = {move: 0 for move in self.possible_moves}
            for move in pattern_dict[recent_sequence]:
                move_counts[move] += 1

            # Predict the most common move
            predicted_move = max(move_counts, key=move_counts.get)
        else:
            # If no pattern found, predict based on overall frequency
            move_counts = {move: player_moves.count(move) for move in self.possible_moves}
            predicted_move = max(move_counts, key=move_counts.get)

        # Choose counter move
        if predicted_move == "rock":
            ai_move = "paper"
        elif predicted_move == "paper":
            ai_move = "scissors"
        else:  # scissors
            ai_move = "rock"

        # Return move and updated state
        return ai_move, {
            "player_last_move": None,
            "player_moves": player_moves,
            "pattern_dict": dict(pattern_dict),  # Convert defaultdict to dict for serialization
            "sequence_length": sequence_length
        }