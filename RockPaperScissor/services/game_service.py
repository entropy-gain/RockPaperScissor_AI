from typing import Dict, Any, Optional, Tuple, List
from ..repositories.game_repository import GameRepository
from ..models.base_ai import BaseAI
from ..models.random_ai import RandomAI
from ..models.pattern_ai import PatternAI
from ..models.adaptive_markov_ai import AdaptiveMarkovAI
from ..utils.logging import setup_logging

logger = setup_logging()

class GameService:
    """Service for game-related logic."""
    
    def __init__(self, game_repository: Optional[GameRepository] = None):
        """Initialize the game service."""
        self.repository = game_repository or GameRepository()
        self.ai_classes = {
            "random": RandomAI,
            "pattern": PatternAI,
            "adaptive": AdaptiveMarkovAI
        }
    
    def start_new_round(self, session_id: Optional[str] = None, user_id: Optional[str] = None, ai_type: str = "adaptive") -> Dict[str, Any]:
        """
        Start a new round, either in an existing session or a new one.
        
        Args:
            session_id: Optional existing session ID
            user_id: Optional user identifier
            ai_type: Type of AI to use
            
        Returns:
            Dictionary with game_id and session_id
        """
        # Validate AI type
        if ai_type not in self.ai_classes:
            ai_type = "adaptive"  # Default to adaptive
        
        # Create new round in repository
        result = self.repository.create_new_round(session_id, user_id, ai_type)
        return result
    
    def play_round(self, game_id: str, player_move: str) -> Dict[str, Any]:
        """
        Play a single round of rock-paper-scissors.
        
        Args:
            game_id: The ID of the current round
            player_move: The player's move ("rock", "paper", or "scissors")
            
        Returns:
            Dict containing round results
        """
        # Validate player move
        valid_moves = ["rock", "paper", "scissors"]
        if player_move not in valid_moves:
            raise ValueError(f"Invalid move: {player_move}. Must be one of {valid_moves}")
        
        # Get game details
        game = self.repository.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
            
        if game.get('round_complete', False):
            raise ValueError(f"This round is already complete")
        
        # Update game with player's move
        self.repository.update_round_with_player_move(game_id, player_move)
        
        # Get AI type and model state
        ai_type = game['ai_type']
        model_state = game.get('model_state', {})
        
        # Create AI instance
        ai_class = self.ai_classes[ai_type]
        ai = ai_class()
        
        # Get AI's move
        ai_move, updated_model_state = ai.make_move(model_state)
        
        # Determine winner
        result = self._determine_winner(player_move, ai_move)

        # Set player's current move in the model state
        model_state["player_last_move"] = player_move
        
        # Complete the round in repository
        self.repository.complete_round(game_id, ai_move, result, updated_model_state)
        
        # Get the updated session stats
        session_id = game['session_id']
        session_stats = self.repository.get_session_stats(session_id)
        
        # Build response
        response = {
            "game_id": game_id,
            "session_id": session_id,
            "player_move": player_move,
            "ai_move": ai_move,
            "result": result,
            "session_stats": session_stats
        }
        
        return response
    
    def _determine_winner(self, player_move: str, ai_move: str) -> str:
        """Determine the winner of a round."""
        if player_move == ai_move:
            return "draw"
        
        # Rock beats scissors, scissors beats paper, paper beats rock
        if (player_move == "rock" and ai_move == "scissors") or \
           (player_move == "scissors" and ai_move == "paper") or \
           (player_move == "paper" and ai_move == "rock"):
            return "player_win"
        
        return "ai_win"
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session."""
        return self.repository.get_session_stats(session_id)
    
    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a user across all sessions."""
        return self.repository.get_user_stats(user_id)
    
    def get_ai_performance_stats(self) -> List[Dict[str, Any]]:
        """Get performance comparisons for different AI types."""
        return self.repository.get_ai_performance()
    
    def get_session_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent rounds in a session."""
        return self.repository.get_session_games(session_id, limit)