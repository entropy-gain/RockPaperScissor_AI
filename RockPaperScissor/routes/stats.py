from fastapi import APIRouter
from RockPaperScissor.database.db import get_user_stats

stats_router = APIRouter()

@stats_router.get("/stats/{user_id}")
async def get_stats(user_id: str):
    """
    Retrieves win/loss/draw statistics for a user.
    """
    return get_user_stats(user_id)
