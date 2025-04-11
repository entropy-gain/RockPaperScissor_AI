from typing import Dict, Any, Optional, Tuple, List
import uuid
from ..repositories.game_repository import GameRepository
from ..schemas.game import GameRequest, GameResponse, GameData
from ..models import get_ai, AI_MODELS
from ..utils.logging import setup_logging

logger = setup_logging()

class GameService:
    """Service for game-related logic."""
    
    def __init__(self, game_repository: Optional[GameRepository] = None):
        """Initialize the game service."""
        self.repository = game_repository or GameRepository()

    def play_round(self, request: GameRequest) -> GameResponse:
        """
        Play a single round of rock-paper-scissors.
        
        Args:
            game_id: The ID of the current round
            user_move: The player's move ("rock", "paper", or "scissors")
            
        Returns:
            Dict containing round results
        """

        # Get game details and model state
        last_game = self.repository.get_latest_game_in_session(request.session_id)

        if not last_game:
            model_state = {}
        else:
            model_state = last_game.get('model_state', {})
        
        # Create AI instance
        ai = get_ai(request.ai_type)

        # Get AI's move
        ai_move, model_state = ai.make_move(model_state)
        
        # Determine winner
        result = self._determine_winner(request.user_move, ai_move)

        # Set player's current move in the model state
        model_state["player_last_move"] = request.user_move
        logger.debug(f"Updated model state: {model_state}")

        # Get the updated session stats
        session_stats = self.update_session_stats(last_game, request.user_move, result)
        
        
        # Create GameData for storage
        game_data = GameData(
            game_id=request.game_id,
            user_id=request.user_id,
            session_id=request.session_id,
            ai_type=request.ai_type,
            user_move=request.user_move,
            ai_move=ai_move,
            result=result,
            model_state=model_state,
            session_stats=session_stats,
        )
        # Save game in repository
        self.repository.save_game(game_data)
        
        
        # Build response
        # Create response
        response = GameResponse(
            game_id=request.game_id,
            user_id=request.user_id,
            session_id=request.session_id,
            user_move=request.user_move,
            ai_type=request.ai_type,
            ai_move=ai_move,
            result=result,
            session_stats=session_stats
            )
        
        return response
    
    def _determine_winner(self, user_move: str, ai_move: str) -> str:
        """Determine the winner of a round."""
        if user_move == ai_move:
            return "draw"
        
        # Rock beats scissors, scissors beats paper, paper beats rock
        if (user_move == "rock" and ai_move == "scissors") or \
           (user_move == "scissors" and ai_move == "paper") or \
           (user_move == "paper" and ai_move == "rock"):
            return "player_win"
        
        return "ai_win"
    
    
    def update_session_stats(self, last_game: Optional[Dict[str, Any]], 
                        user_move: str, result: str) -> Dict[str, Any]:
        """
        Update session statistics based on current game result and last game's stats.
        
        Args:
            last_game: The previous game data with session stats
            user_move: The current player move
            result: The result of the current round
            
        Returns:
            Updated session statistics
        """
        # Get previous stats or initialize new stats
        if last_game and "session_stats" in last_game:
            stats = last_game.get("session_stats", {}).copy()
        else:
            stats = {
                "total_games": 0,
                "player_wins": 0,
                "ai_wins": 0,
                "draws": 0,
                "player_rock_count": 0,  # Use consistent naming scheme
                "player_paper_count": 0,
                "player_scissors_count": 0,
                "player_win_rate": 0,
                "ai_win_rate": 0,
                "current_player_win_streak": 0
            }
        
        # Increment total games
        stats["total_games"] = stats.get("total_games", 0) + 1
        
        # Update result counters
        if result == "player_win":
            stats["player_wins"] = stats.get("player_wins", 0) + 1
            stats["current_player_win_streak"] = stats.get("current_player_win_streak", 0) + 1
        elif result == "ai_win":
            stats["ai_wins"] = stats.get("ai_wins", 0) + 1
            stats["current_player_win_streak"] = 0  # Reset streak on loss
        elif result == "draw":
            stats["draws"] = stats.get("draws", 0) + 1
            # Optionally reset streak on draw, depending on your game rules
        
        # Update move counters with consistent key names
        if user_move == "rock":
            stats["player_rock_count"] = stats.get("player_rock_count", 0) + 1
        elif user_move == "paper":
            stats["player_paper_count"] = stats.get("player_paper_count", 0) + 1
        elif user_move == "scissors":
            stats["player_scissors_count"] = stats.get("player_scissors_count", 0) + 1
        
        # Calculate win rates
        if stats["total_games"] > 0:
            stats["player_win_rate"] = (stats.get("player_wins", 0) / stats["total_games"]) * 100
            stats["ai_win_rate"] = (stats.get("ai_wins", 0) / stats["total_games"]) * 100
        else:
            stats["player_win_rate"] = 0
            stats["ai_win_rate"] = 0
            
        return stats
    
    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a user across all sessions."""
        return self.repository.get_user_stats(user_id)
    
    def get_ai_performance_stats(self) -> List[Dict[str, Any]]:
        """Get performance comparisons for different AI types."""
        return self.repository.get_ai_performance()
    
    def get_session_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent rounds in a session."""
        return self.repository.get_session_games(session_id, limit)