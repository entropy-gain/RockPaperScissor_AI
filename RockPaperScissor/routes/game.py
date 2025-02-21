# backend/routes/game.py
from fastapi import APIRouter
from RockPaperScissor.database.db import save_game, get_user_stats
from RockPaperScissor.models.ai_manager import get_ai
from RockPaperScissor.schemas.game import GameRequest, GameResponse


game_router = APIRouter()
    
@game_router.post("/play")
async def play_game(request: GameRequest):
    """
    Handles a game round, saving the result in the database.
    """
    ai = get_ai(request.ai_type)
    history = get_user_stats(request.user_id) 
    ai_move = ai.make_move(history)  # Implement history-based AI selection if needed

    result = "win" if (request.user_move == "rock" and ai_move == "scissors") or \
                     (request.user_move == "paper" and ai_move == "rock") or \
                     (request.user_move == "scissors" and ai_move == "paper") else "lose" if request.user_move != ai_move else "draw"
    save_game(request.user_id, request.user_move, ai_move, request.ai_type, result)
    # return {"user": request.user_move, "ai": ai_move, "result": result}
    return GameResponse(user_move=request.user_move, ai_move=ai_move, result=result)