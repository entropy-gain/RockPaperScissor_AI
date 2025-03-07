from .base_ai import BaseAI
import math
import numpy as np
from collections import defaultdict

class AdaptiveMarkovAI(BaseAI):
    """
    Adaptive RPS AI that uses entropy-based weighting between Markov and Frequency models.
    
    This model uses two prediction strategies:
    1. Markov model: Captures sequential patterns in player moves
    2. Frequency model: Captures overall move distribution
    
    The models are weighted adaptively using entropy as the key metric of predictability.
    """
    def __init__(self, smoothing_factor=1.0, temperature=1.0):
        # Move mapping for internal calculations
        self.moves = ["rock", "paper", "scissors"]
        self.move_to_idx = {"rock": 0, "paper": 1, "scissors": 2}
        self.idx_to_move = {0: "rock", 1: "paper", 2: "scissors"}
        self.counters = {"rock": "paper", "paper": "scissors", "scissors": "rock"}
        
        # Initialize models with smoothing
        self.smoothing = smoothing_factor
        self.markov_counts = np.ones((3, 3)) * self.smoothing  # [prev_move][next_move]
        self.frequency_counts = np.ones(3) * self.smoothing
        
        # Lambda adjustment parameters
        self.temperature = temperature  # Controls sensitivity to entropy differences
        
        # Internal tracking
        self._history = []  # For internal decision making
        self._last_lambdas = {"markov": 0.5, "freq": 0.5}  # Default equal weights
    
    def calculate_entropy(self, probs):
        """Calculate Shannon entropy of a probability distribution"""
        entropy = 0
        for p in probs:
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy
    
    def get_markov_probabilities(self, prev_move):
        """Get transition probabilities from the Markov model"""
        if prev_move not in self.move_to_idx:
            # Default to uniform if unknown move
            return [1/3, 1/3, 1/3]
        
        prev_idx = self.move_to_idx[prev_move]
        row_sum = np.sum(self.markov_counts[prev_idx])
        return self.markov_counts[prev_idx] / row_sum
    
    def get_frequency_probabilities(self):
        """Get overall move probabilities from the frequency model"""
        total = np.sum(self.frequency_counts)
        return self.frequency_counts / total
    
    def update_models(self, prev_move, curr_move):
        """Update model counts with new move information"""
        if prev_move in self.move_to_idx and curr_move in self.move_to_idx:
            prev_idx = self.move_to_idx[prev_move]
            curr_idx = self.move_to_idx[curr_move]
            
            # Update transition counts
            self.markov_counts[prev_idx][curr_idx] += 1
        
        # Update frequency counts
        if curr_move in self.move_to_idx:
            curr_idx = self.move_to_idx[curr_move]
            self.frequency_counts[curr_idx] += 1
    
    def calculate_lambdas(self, markov_probs, freq_probs):
        """
        Calculate adaptive weights using entropy-based formula:
        λ_M = e^(-T*H_M) / (e^(-T*H_M) + e^(-T*H_F))
        λ_F = e^(-T*H_F) / (e^(-T*H_M) + e^(-T*H_F))
        
        Where T is temperature parameter
        """
        # Calculate entropies
        markov_entropy = self.calculate_entropy(markov_probs)
        freq_entropy = self.calculate_entropy(freq_probs)
        
        # Apply temperature and calculate weights
        denom = math.exp(-self.temperature * markov_entropy) + math.exp(-self.temperature * freq_entropy)
        lambda_markov = math.exp(-self.temperature * markov_entropy) / denom
        lambda_freq = math.exp(-self.temperature * freq_entropy) / denom
        
        # Store for potential logging/debugging
        self._last_lambdas = {
            "markov": lambda_markov,
            "freq": lambda_freq,
            "markov_entropy": markov_entropy,
            "freq_entropy": freq_entropy
        }
        
        return lambda_markov, lambda_freq
    
    def make_move(self, history):
        """
        Predict player's next move and return the counter move.
        
        Args:
            history (dict): Dictionary containing player move counts
                Example: {"rock": 3, "paper": 2, "scissors": 1}
        
        Returns:
            str: The AI's chosen move (rock, paper, or scissors)
        """
        # Process history into our format if needed
        if isinstance(history, dict):
            # Convert external history format (from game.py) to our internal format
            # This is needed to handle the interface with the existing system
            # Store the count of each move type
            for move, count in history.items():
                if move in self.move_to_idx:
                    self.frequency_counts[self.move_to_idx[move]] = count + self.smoothing
        
        # If no internal history, make a random move
        if not self._history:
            predicted_move = np.random.choice(self.moves)
            return self.counters[predicted_move]
        
        # Get previous move for Markov prediction
        prev_move = self._history[-1]
        
        # Get probabilities from each model
        markov_probs = self.get_markov_probabilities(prev_move)
        freq_probs = self.get_frequency_probabilities()
        
        # Calculate adaptive lambda weights
        lambda_markov, lambda_freq = self.calculate_lambdas(markov_probs, freq_probs)
        
        # Combine predictions with lambda weights
        combined_probs = lambda_markov * markov_probs + lambda_freq * freq_probs
        
        # Predict most likely move
        predicted_move = self.idx_to_move[np.argmax(combined_probs)]
        
        # Return counter move to beat the prediction
        return self.counters[predicted_move]
    
    def update_history(self, player_move):
        """Update internal history with player's actual move"""
        # If we have a previous move, update transition models
        if self._history:
            prev_move = self._history[-1]
            self.update_models(prev_move, player_move)
        
        # Append to history
        self._history.append(player_move)
    
    def get_lambdas(self):
        """Return current lambda weights (for monitoring/debugging)"""
        return self._last_lambdas