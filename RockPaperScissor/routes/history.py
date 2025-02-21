from fastapi import APIRouter
from RockPaperScissor.database.db import get_game_history

history_router = APIRouter()

@history_router.get("/history")
async def get_history(user_id: str):
    """
    Retrieves the game history for a user.
    """
    return get_game_history()