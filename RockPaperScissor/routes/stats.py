"""
Statistics routes module for RockPaperScissor game.
Provides endpoints for game statistics and analytics.
"""
from fastapi import APIRouter, HTTPException, Path
from typing import List, Dict, Any, Optional
from RockPaperScissor.services import GameService
from RockPaperScissor.schemas.game import GameRequest, GameResponse
from RockPaperScissor.utils.logging import setup_logging

# Set up logger
logger = setup_logging()


stats_router = APIRouter()


@stats_router.get("/")
async def get_game_stats(request: GameRequest):
    """
    Get overall game statistics
    
    Returns statistics for players and AI models
    """
    try:
        # Log the request
        # logger.info(f"Game request: {request.model_dump()}")

        # Create service instance
        game_service = GameService()
        logger.info("GameService created")
    except:
        raise




@stats_router.get("/")
async def get_game_stats():
    """
    Get overall game statistics
    
    Returns statistics for players and AI models
    """
    try:
        # Since we don't have actual database stats yet, return mock data
        return {
            "players": [
                {
                    "name": "test_user",
                    "total_games": 12,
                    "wins": 5,
                    "losses": 5,
                    "draws": 2,
                    "win_rate": 41.7
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@stats_router.get("/{user_id}")
async def get_user_stats(user_id: str = Path(..., title="The ID of the user to get stats for")):
    """
    Get statistics for a specific user
    
    Returns detailed statistics for the specified user
    """
    try:
        # Mock data for user stats
        return {
            "user_id": user_id,
            "total_games": 12,
            "wins": 5,
            "losses": 5,
            "draws": 2,
            "win_rate": 41.7,
            "moves": {
                "rock": 5,
                "paper": 4,
                "scissors": 3
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@stats_router.get("/ai-performance")
async def get_ai_performance():
    """
    Get performance statistics for all AI models
    
    Returns a list of AI models with their performance metrics
    """
    try:
        # Return mock AI performance data
        return [
            {"name": "adaptive_markov", "win_rate": 99, "wins": 5, "losses": 2, "draws": 1},
            {"name": "pattern", "win_rate": 50.0, "wins": 3, "losses": 3, "draws": 0},
            {"name": "markov", "win_rate": 40.0, "wins": 2, "losses": 3, "draws": 0},
            {"name": "random", "win_rate": 33.3, "wins": 2, "losses": 4, "draws": 0}
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))