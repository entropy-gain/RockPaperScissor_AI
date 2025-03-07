from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
from RockPaperScissor.database.db import get_user_stats

# Create models for the stats API response
class PlayerStats(BaseModel):
    name: str
    total_games: int
    wins: int
    losses: int
    draws: int
    win_rate: float

class AiModelStats(BaseModel):
    name: str
    total_games: int
    wins: int
    losses: int
    draws: int
    win_rate: float

class GameStats(BaseModel):
    players: List[PlayerStats]
    ai_models: List[AiModelStats]
    total_games_played: int

# Initialize the router
stats_router = APIRouter()

# Keep your existing endpoint for individual user stats
@stats_router.get("/stats/{user_id}")
async def get_stats(user_id: str):
    """
    Retrieves win/loss/draw statistics for a user.
    """
    return get_user_stats(user_id)

# Add a new endpoint for overall game stats (all players and AI models)
@stats_router.get("/stats", response_model=GameStats)
async def get_game_stats():
    """
    Retrieves comprehensive game statistics for all players and AI models.
    """
    from RockPaperScissor.database.db import get_all_users_stats, get_all_ai_stats, get_total_games
    
    # Get all user stats from your database
    all_users = get_all_users_stats()
    
    # Get all AI model stats
    all_ai_models = get_all_ai_stats()
    
    # Get total games played
    total_games = get_total_games()
    
    # Convert to response model format
    players = []
    for user in all_users:
        # Calculate win rate
        total_user_games = user["wins"] + user["losses"] + user["draws"]
        win_rate = (user["wins"] / total_user_games * 100) if total_user_games > 0 else 0
        
        players.append(PlayerStats(
            name=user["user_id"],
            total_games=total_user_games,
            wins=user["wins"],
            losses=user["losses"],
            draws=user["draws"],
            win_rate=win_rate
        ))
    
    # Convert AI stats
    ai_models = []
    for ai in all_ai_models:
        # Calculate win rate
        total_ai_games = ai["wins"] + ai["losses"] + ai["draws"]
        win_rate = (ai["wins"] / total_ai_games * 100) if total_ai_games > 0 else 0
        
        ai_models.append(AiModelStats(
            name=ai["ai_type"],
            total_games=total_ai_games,
            wins=ai["wins"],
            losses=ai["losses"],
            draws=ai["draws"],
            win_rate=win_rate
        ))
    
    return GameStats(
        players=players,
        ai_models=ai_models,
        total_games_played=total_games
    )