from typing import Dict, Any, Optional, Tuple
import random
import numpy as np

from .base_ai import BaseAI


class QLearningAI(BaseAI):
    """
    Q-Learning based AI for Rock-Paper-Scissors.

    Uses reinforcement learning to learn optimal strategy based on player patterns.
    State is defined by the last N player moves, and Q-values are updated based on game outcomes.
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        epsilon: float = 0.2,
        state_history_length: int = 2
    ):
        """
        Initialize Q-Learning AI.

        Args:
            learning_rate: Learning rate (alpha) for Q-value updates (0-1)
            discount_factor: Discount factor (gamma) for future rewards (0-1)
            epsilon: Exploration rate for epsilon-greedy policy (0-1)
            state_history_length: Number of previous moves to consider as state
        """
        super().__init__()
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.state_history_length = state_history_length

    def make_move(self, model_state: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Generate AI's next move using Q-learning algorithm.

        Args:
            model_state: Dictionary containing:
                - q_table: Q-values for state-action pairs
                - player_move_history: List of recent player moves
                - last_state: Previous state representation
                - last_action: Previous action taken by AI
                - last_result: Result of last game ("player_win", "ai_win", "draw")
                - learning_rate: Learning rate
                - discount_factor: Discount factor
                - epsilon: Exploration rate

        Returns:
            Tuple containing:
            - str: AI's chosen move (rock, paper, scissors)
            - Dict: Updated model state
        """
        # Initialize model state if None
        if model_state is None:
            model_state = self._initialize_state()

        # Extract values from model state
        q_table = model_state.get("q_table", {})
        player_move_history = model_state.get("player_move_history", [])
        last_state = model_state.get("last_state")
        last_action = model_state.get("last_action")
        last_result = model_state.get("last_result")
        player_last_move = model_state.get("player_last_move")

        # Update Q-table with feedback from last round (if available)
        if last_state is not None and last_action is not None and last_result is not None:
            # Convert result to reward
            reward = self._result_to_reward(last_result)

            # Update player move history
            if player_last_move:
                player_move_history.append(player_last_move)
                # Keep only the most recent moves
                if len(player_move_history) > self.state_history_length:
                    player_move_history = player_move_history[-self.state_history_length:]

            # Get current state after player's move
            current_state = self._encode_state(player_move_history)

            # Q-learning update: Q(s,a) = Q(s,a) + α * [r + γ * max_a' Q(s',a') - Q(s,a)]
            current_q = q_table.get(last_state, {}).get(last_action, 0.0)
            max_future_q = self._get_max_q_value(q_table, current_state)
            new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_future_q - current_q)

            # Update Q-table
            if last_state not in q_table:
                q_table[last_state] = {}
            q_table[last_state][last_action] = new_q
        else:
            # First move or no previous result - just update history if player made a move
            if player_last_move:
                player_move_history.append(player_last_move)
                if len(player_move_history) > self.state_history_length:
                    player_move_history = player_move_history[-self.state_history_length:]

        # Get current state for action selection
        current_state = self._encode_state(player_move_history)

        # Select action using epsilon-greedy policy
        action = self._select_action(q_table, current_state)

        # Prepare updated state
        updated_state = {
            "q_table": q_table,
            "player_move_history": player_move_history,
            "last_state": current_state,
            "last_action": action,
            "last_result": None,  # Will be updated by service layer
            "player_last_move": None,  # Will be updated by service layer
            "ai_last_move": action,
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "epsilon": self.epsilon,
            "state_history_length": self.state_history_length
        }

        return action, updated_state

    def _initialize_state(self) -> Dict[str, Any]:
        """Initialize a new model state."""
        return {
            "q_table": {},
            "player_move_history": [],
            "last_state": None,
            "last_action": None,
            "last_result": None,
            "player_last_move": None,
            "ai_last_move": None,
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "epsilon": self.epsilon,
            "state_history_length": self.state_history_length
        }

    def _encode_state(self, move_history: list) -> str:
        """
        Encode move history into a state string.

        Args:
            move_history: List of recent player moves

        Returns:
            String representation of state (e.g., "rock,paper" for last 2 moves)
        """
        if not move_history:
            return "START"

        # Use last N moves as state
        recent_moves = move_history[-self.state_history_length:]
        return ",".join(recent_moves)

    def _result_to_reward(self, result: str) -> float:
        """
        Convert game result to reward value.

        Args:
            result: Game result ("player_win", "ai_win", "draw")

        Returns:
            Reward value (1.0 for win, -1.0 for loss, 0.0 for draw)
        """
        if result == "ai_win":
            return 1.0
        elif result == "player_win":
            return -1.0
        else:  # draw
            return 0.0

    def _get_max_q_value(self, q_table: Dict[str, Dict[str, float]], state: str) -> float:
        """
        Get maximum Q-value for a given state.

        Args:
            q_table: Q-table dictionary
            state: State string

        Returns:
            Maximum Q-value across all actions for this state
        """
        if state not in q_table or not q_table[state]:
            return 0.0
        return max(q_table[state].values())

    def _select_action(self, q_table: Dict[str, Dict[str, float]], state: str) -> str:
        """
        Select action using epsilon-greedy policy.

        Args:
            q_table: Q-table dictionary
            state: Current state string

        Returns:
            Selected action (rock, paper, or scissors)
        """
        # Epsilon-greedy: explore with probability epsilon, exploit otherwise
        if random.random() < self.epsilon:
            # Explore: random action
            return random.choice(self.possible_moves)
        else:
            # Exploit: choose action with highest Q-value
            if state not in q_table or not q_table[state]:
                # No Q-values yet, choose randomly
                return random.choice(self.possible_moves)

            # Get action with maximum Q-value
            state_q_values = q_table[state]
            max_q = max(state_q_values.values())

            # Get all actions with maximum Q-value (in case of ties)
            best_actions = [action for action, q_value in state_q_values.items() if q_value == max_q]

            return random.choice(best_actions)
