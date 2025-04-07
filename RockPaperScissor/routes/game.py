# backend/routes/game.py
from fastapi import APIRouter, HTTPException
from RockPaperScissor.services import GameService
from RockPaperScissor.schemas.game import GameRequest, GameResponse, NewGameResponse
from RockPaperScissor.utils.logging import setup_logging

# Set up logger
logger = setup_logging()

game_router = APIRouter()

@game_router.post("/start")
async def start_new_round(request: GameRequest):
    """
    Start a new round in a session.
    """
    try:
        # Log the request
        logger.info(f"New round request: {request.model_dump()}")

        # Create service instance
        game_service = GameService()
        
        # Call service method to start a new round
        result = game_service.start_new_round(
            session_id=request.session_id,
            user_id=request.user_id,
            ai_type=request.ai_type
        )
        
        # Return new game information
        return NewGameResponse(
            game_id=result['game_id'],
            session_id=result['session_id']
        )
    
    except Exception as e:
        logger.error(f"Error starting new round: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while starting a new round"
        )
    
@game_router.post("/play")
async def play_round(request: GameRequest):
    """
    Play a round with the player's move.
    """
    try:
        # Log the request
        logger.info(f"Play round request: {request.model_dump()}")

        # Create service instance
        game_service = GameService()
        
        # Call service method to play the round
        result = game_service.play_round(
            game_id=request.game_id,
            player_move=request.user_move
        )
        
        # Convert service result to response model
        return GameResponse(
            game_id=result['game_id'],
            session_id=result['session_id'],
            user_move=result['player_move'],
            ai_move=result['ai_move'],
            result=result['result'],
            session_stats=result['session_stats']
        )
    
    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing round: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the round"
        )

@game_router.get("/session/{session_id}/stats")
async def get_session_stats(session_id: str):
    """
    Get statistics for a specific session.
    """
    try:
        game_service = GameService()
        stats = game_service.get_session_stats(session_id)
        return stats
    except Exception as e:
        logger.error(f"Error retrieving session stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving session statistics"
        )
    
@game_router.get("/user/{user_id}/stats")
async def get_user_stats(user_id: str):
    """
    Get statistics for a specific user across all sessions.
    """
    try:
        game_service = GameService()
        stats = game_service.get_user_statistics(user_id)
        return stats
    except Exception as e:
        logger.error(f"Error retrieving user stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving user statistics"
        )
    
@game_router.get("/ai-performance")
async def get_ai_performance():
    """
    Get performance statistics for all AI models.
    """
    try:
        game_service = GameService()
        ai_performance = game_service.get_ai_performance_stats()
        return ai_performance
    except Exception as e:
        logger.error(f"Error retrieving AI performance: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving AI performance data"
        )

@game_router.get("/session/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 10):
    """
    Get the history of rounds for a specific session.
    """
    try:
        game_service = GameService()
        history = game_service.get_session_history(session_id, limit)
        return history
    except Exception as e:
        logger.error(f"Error retrieving session history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving session history"
        )