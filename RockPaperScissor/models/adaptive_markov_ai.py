from typing import Dict, Any, Optional, Tuple
import math
import numpy as np

from .base_ai import BaseAI

class AdaptiveMarkovAI(BaseAI):
    """
    Adaptive RPS AI that uses entropy-based weighting between Markov and Frequency models.
    """
    def __init__(self, smoothing_factor=1.0, temperature=1.0):
        super().__init__()
        self.smoothing = smoothing_factor
        self.temperature = temperature

    def make_move(self, model_state: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Generate AI's next move based on model state.
        
        Args:
            model_state: Dictionary containing:
                - markov_counts: Transition count matrix
                - frequency_counts: Overall frequency counts
                - player_last_move: The player's last move from previous round
                - smoothing: Smoothing factor for probability calculations
                - temperature: Temperature parameter for entropy weighting
                - last_lambdas: Last calculated model weights
                
        Returns:
            Tuple containing:
            - str: AI's chosen move (rock, paper, scissors)
            - Dict: Updated model state (ready for next round after player moves)
        """
        # Initialize model state if None
        if model_state is None:
            model_state = {
                "markov_counts": np.ones((3, 3)) * self.smoothing,
                "frequency_counts": np.ones(3) * self.smoothing,
                "player_last_move": None,
                "player_second_last_move": None,
                "smoothing": self.smoothing,
                "temperature": self.temperature,
                "last_lambdas": {"markov": 0.5, "freq": 0.5}
            }
        
        # Extract values from model state
        markov_counts = model_state.get("markov_counts", np.ones((3, 3)) * self.smoothing)
        frequency_counts = model_state.get("frequency_counts", np.ones(3) * self.smoothing)
        player_last_move = model_state.get("player_last_move")
        player_second_last_move = model_state.get("player_second_last_move")
        smoothing = model_state.get("smoothing", self.smoothing)
        temperature = model_state.get("temperature", self.temperature)
        last_lambdas = model_state.get("last_lambdas", {"markov": 0.5, "freq": 0.5})
        
        # Define move mappings
        move_to_idx = {"rock": 0, "paper": 1, "scissors": 2}
        idx_to_move = {0: "rock", 1: "paper", 2: "scissors"}
        counters = {"rock": "paper", "paper": "scissors", "scissors": "rock"}
        
        # Helper functions
        def calculate_entropy(probs):
            """Calculate Shannon entropy of a probability distribution"""
            entropy = 0
            for p in probs:
                if p > 0:
                    entropy -= p * math.log2(p)
            return entropy
        
        def get_markov_probabilities(move):
            """Get transition probabilities from the Markov model"""
            if move not in move_to_idx:
                # Default to uniform if unknown move
                return [1/3, 1/3, 1/3]
            
            move_idx = move_to_idx[move]
            row_sum = np.sum(markov_counts[move_idx])
            return markov_counts[move_idx] / row_sum
        
        def get_frequency_probabilities():
            """Get overall move probabilities from the frequency model"""
            total = np.sum(frequency_counts)
            return frequency_counts / total
        
        def calculate_lambdas(markov_probs, freq_probs):
            """Calculate adaptive weights using entropy-based formula"""
            # Calculate entropies
            markov_entropy = calculate_entropy(markov_probs)
            freq_entropy = calculate_entropy(freq_probs)
            
            # Apply temperature and calculate weights
            denom = math.exp(-temperature * markov_entropy) + math.exp(-temperature * freq_entropy)
            lambda_markov = math.exp(-temperature * markov_entropy) / denom
            lambda_freq = math.exp(-temperature * freq_entropy) / denom
            
            # Return weights and entropy values for monitoring
            return lambda_markov, lambda_freq, {
                "markov": lambda_markov,
                "freq": lambda_freq,
                "markov_entropy": markov_entropy,
                "freq_entropy": freq_entropy
            }
        
        # Update the models with historical data if available
        if player_last_move and player_last_move in move_to_idx:
            # Update frequency counts
            last_idx = move_to_idx[player_last_move]
            frequency_counts[last_idx] += 1
            
            # Update Markov model if we have two consecutive moves
            if player_second_last_move and player_second_last_move in move_to_idx:
                second_last_idx = move_to_idx[player_second_last_move]
                markov_counts[second_last_idx][last_idx] += 1
        
        # For prediction, use player_last_move for Markov model
        if player_last_move is None:
            # No history yet, use random prediction
            predicted_move = np.random.choice(self.possible_moves)
        else:
            # Get probabilities from each model
            markov_probs = get_markov_probabilities(player_last_move)
            freq_probs = get_frequency_probabilities()
            
            # Calculate adaptive lambda weights
            lambda_markov, lambda_freq, new_lambdas = calculate_lambdas(markov_probs, freq_probs)
            
            # Combine predictions with lambda weights
            combined_probs = lambda_markov * np.array(markov_probs) + lambda_freq * np.array(freq_probs)
            
            # Predict most likely move
            predicted_idx = np.argmax(combined_probs)
            predicted_move = idx_to_move[predicted_idx]
            
            # Update lambdas in state
            last_lambdas = new_lambdas
        
        # Prepare updated state
        updated_state = {
            "markov_counts": markov_counts,
            "frequency_counts": frequency_counts,
            "player_last_move": None,  # Keep until service layer updates it
            "player_second_last_move": player_last_move,  # Keep until service layer updates it
            "smoothing": smoothing,
            "temperature": temperature,
            "last_lambdas": last_lambdas
        }
        
        # Return counter move and updated state
        return counters[predicted_move], updated_state