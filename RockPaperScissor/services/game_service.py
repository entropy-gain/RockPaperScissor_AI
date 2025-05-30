# RockPaperScissor/services/game_service.py
from typing import Dict, Any, Optional, Tuple
import asyncio
import uuid
from ..schemas.game import GameRequest, GameResponse
from ..models import get_ai
from ..repositories.storage import Storage
from ..game_cache.memory_cache import GameSessionCache

class GameService:
    def __init__(self, storage: Storage):
        self.storage = storage
        self.cache = GameSessionCache()
        
    async def initialize(self):
        """Initialize the game service"""
        await self.storage.initialize()
        
    async def play_round(self, request: GameRequest) -> GameResponse:
        """Play a round of the game"""
        # Get or create session
        session_id = request.session_id
        if not session_id:
            session_id = f"session_{uuid.uuid4()}"
            
        # Get AI instance
        ai_type = request.ai_type or "random"
        ai_instance = get_ai(ai_type)
        
        # Get AI state from storage
        ai_state = await self.storage.get_ai_state(session_id, ai_type)
        
        # Make AI move
        ai_move, new_ai_state = ai_instance.make_move(ai_state)
        
        # Determine result
        result = self._determine_winner(request.player_move, ai_move)
        
        # Prepare game data for storage
        game_data = {
            'game_id': session_id,
            'player_move': request.player_move,
            'ai_move': ai_move,
            'result': result,
            'ai_type': ai_type,
            'ai_state': new_ai_state
        }
        
        # Save to storage
        await self.storage.save_game_round(game_data)
        
        # Update cache
        self.cache.update_session(session_id, game_data)
        
        # Get updated stats
        stats = await self.storage.get_game_history(session_id)
        
        return GameResponse(
            session_id=session_id,
            player_move=request.player_move,
            ai_move=ai_move,
            result=result,
            stats=stats
        )
        
    def _determine_winner(self, player_move: str, ai_move: str) -> str:
        """Determine the winner of a round"""
        if player_move == ai_move:
            return "draw"
            
        winning_moves = {
            "rock": "scissors",
            "paper": "rock",
            "scissors": "paper"
        }
        
        return "player_win" if winning_moves[player_move] == ai_move else "ai_win"
        
    async def close(self):
        """Close the game service"""
        await self.storage.close()
        self.cache.clear()