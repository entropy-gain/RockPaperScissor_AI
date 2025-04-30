from typing import Dict, Any, Optional
from ..game_cache import GameSessionCache
from ..schemas.game import GameRequest, GameResponse, GameData, GameSummary
from ..models import get_ai
from ..utils import setup_logging
from ..services import LLMService
from ..repositories import Storage

logger = setup_logging()

class GameService:
    """Service for game-related logic."""
    def __init__(self, storage: Storage):
        """Initialize the game service."""
        self.game_cache = GameSessionCache(storage=storage)
        self.llm_service = LLMService(storage)
        self.storage = storage

    def play_round(self, request: GameRequest) -> GameResponse:
        """
        Play a single round of rock-paper-scissors.
        
        Args:
            request: GameRequest object containing game information
            
        Returns:
            GameResponse containing round results
        """

        # Get model info
        model_name, model_state = self._get_model_info(request.session_id, request.user_id)

        # Create AI instance
        ai = get_ai(model_name)

        # Get AI's move
        ai_move, model_state = ai.make_move(model_state)
        
        # Determine winner
        result = self._determine_winner(request.user_move, ai_move)

        # Update model state with game information
        model_state.update({
            "player_last_move": request.user_move,
            "ai_last_move": ai_move,
            "last_result": result
        })
        logger.debug(f"Updated model state: {model_state}")

        # Get the latest record
        latest_record = self.game_cache.get_latest_record(request.session_id)
        # Get the updated session stats
        session_stats = self._update_session_stats(latest_record.session_stats if latest_record else None, request.user_move, result)
        
        # Create GameData for storage
        game_data = GameData(
            game_id=request.game_id,
            user_id=request.user_id,
            session_id=request.session_id,
            user_move=request.user_move,
            ai_move=ai_move,
            result=result,
            model_name=model_name,
            model_state=model_state,
            session_stats=session_stats,
        )
        # Save game in repository
        self.game_cache.add_record(request.session_id, game_data)
        
        # Build response
        response = GameResponse(
            game_id=request.game_id,
            user_id=request.user_id,
            session_id=request.session_id,
            ai_move=ai_move,
            result=result,
            session_stats=session_stats
        )
        
        return response
    
    def end_game(self, request: GameRequest) -> GameSummary:
        """End the game and get summary."""

        # Get latest record for summary
        latest_record = self.game_cache.get_latest_record(request.session_id)
        if latest_record:
            llm_game_summary = self.llm_service.summarize_game_session(latest_record.model_state)

            # Move session data to buffer (will be automatically flushed later)
            self.game_cache.move_session_to_buffer(request.session_id)
        else:
            llm_game_summary = "No game data available for summary"
            
        response = GameSummary(
            game_summary=llm_game_summary,
        )
 
        return response
    
    def _determine_winner(self, player_move: str, ai_move: str) -> str:
        """Determine the winner of a round."""
        if player_move == ai_move:
            return "draw"
        
        winning_moves = {
            "rock": "scissors",
            "paper": "rock",
            "scissors": "paper"
        }
        
        if winning_moves[player_move] == ai_move:
            return "player_win"
        return "ai_win"
    
    def _get_model_info(self, session_id: str, user_id: str) -> tuple[str, Dict[str, Any]]:
            """Get model name and state from cache or storage.
            
            Args:
                session_id: Current session ID
                user_id: User ID
                
            Returns:
                Tuple containing model name and model state
            """
            # get data from cache
            latest_record = self.game_cache.get_latest_record(session_id)

            # get model state from cache or storage
            if latest_record:
                model_name = latest_record.model_name
                model_state = latest_record.model_state
            else:
                # Try to get from storage
                user_state = self.storage.get_user_state(user_id)
                if user_state:
                    model_name = user_state["model_name"]
                    model_state = user_state["model_state"]
                else:
                    model_name = "adaptive_markov"
                    model_state = {}
            
            return model_name, model_state
    
    def _update_session_stats(self, current_stats: Optional[Dict[str, Any]], player_move: str, result: str) -> Dict[str, Any]:
        """Update session statistics."""
        if not current_stats:
            current_stats = {
                "total_rounds": 0,
                "player_wins": 0,
                "ai_wins": 0,
                "draws": 0,
                "rock_count": 0,
                "paper_count": 0,
                "scissors_count": 0
            }
        
        current_stats["total_rounds"] += 1
        if result == "player_win":
            current_stats["player_wins"] += 1
        elif result == "ai_win":
            current_stats["ai_wins"] += 1
        else:
            current_stats["draws"] += 1
            
        # Update move statistics
        if player_move == "rock":
            current_stats["rock_count"] += 1
        elif player_move == "paper":
            current_stats["paper_count"] += 1
        elif player_move == "scissors":
            current_stats["scissors_count"] += 1
            
        return current_stats
    
    async def shutdown(self):
        """Gracefully shutdown the game service."""
        await self.game_cache.shutdown()



