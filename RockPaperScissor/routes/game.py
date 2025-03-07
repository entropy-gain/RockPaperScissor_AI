# backend/routes/game.py
from fastapi import APIRouter
from RockPaperScissor.database.db import save_game, get_user_stats
from RockPaperScissor.models.ai_manager import get_ai
from RockPaperScissor.schemas.game import GameRequest, GameResponse
from RockPaperScissor.models.adaptive_markov_ai import AdaptiveMarkovAI

game_router = APIRouter()

# Store AI instances by user and type to maintain state across requests
ai_instances = {}
    
@game_router.post("/play")
async def play_game(request: GameRequest):
    """
    Handles a game round, saving the result in the database.
    
    Args:
        request (GameRequest): Contains user_id, user_move, and ai_type
        
    Returns:
        GameResponse: Contains user_move, ai_move, and result
    """
    # Create a unique key for this user + AI type combination
    instance_key = f"{request.user_id}_{request.ai_type}"
    
    # Get or create AI instance
    if instance_key not in ai_instances:
        ai_instances[instance_key] = get_ai(request.ai_type)
    
    ai = ai_instances[instance_key]
    
    # Get user stats for AI decision making
    history = get_user_stats(request.user_id) 
    
    # Get AI's move based on history
    ai_move = ai.make_move(history)
    
    # Handle special case for AdaptiveMarkovAI to update its internal history
    if isinstance(ai, AdaptiveMarkovAI):
        ai.update_history(request.user_move)
    
    # Determine the result
    result = "win" if (request.user_move == "rock" and ai_move == "scissors") or \
                     (request.user_move == "paper" and ai_move == "rock") or \
                     (request.user_move == "scissors" and ai_move == "paper") else "lose" if request.user_move != ai_move else "draw"
    
    # Save game to database
    save_game(request.user_id, request.user_move, ai_move, request.ai_type, result)
    
    return GameResponse(user_move=request.user_move, ai_move=ai_move, result=result)