# backend/routes/game.py
from fastapi import APIRouter, HTTPException, Request
from RockPaperScissor.schemas.game import GameRequest, GameResponse  #, GameSummary, LLMRequest
from RockPaperScissor.utils.logging import setup_logging
# from RockPaperScissor.repositories import CombinedStorage  # Persistent storage (commented for Hugging Face)
from RockPaperScissor.services.service_instance import game_service

# Set up logger
logger = setup_logging()

game_router = APIRouter()

@game_router.post("/play")
async def play_round(request: Request, game_request: GameRequest):
    """
    Play a round with the player's move (in-memory only for Hugging Face)
    """
    return await game_service.play_round(game_request.session_id, game_request.player_move, game_request.ai_type)

# @game_router.post("/analyze")
# async def analyze_game_state(llm_request: LLMRequest):
#     """
#     Get LLM analysis of the current game state.
#     """
#     try:
#         # Log the request
#         logger.info(f"Analyze request: {llm_request.model_dump()}")
#         
#         # Get LLM analysis directly from LLM service
#         analysis = llm_service.analyze_game_state(llm_request)
#         return {"analysis": analysis}
#         
#     except Exception as e:
#         logger.error(f"Error analyzing game state: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail="An error occurred while analyzing the game state"
#         )

@game_router.post("/end")
async def end_game(request: Request):
    """
    End the current game session and save the final state.
    """
    try:
        data = await request.json()
        session_id = data.get('session_id')
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="No session ID provided"
            )
        # Mark session as completed in storage (commented for Hugging Face)
        # await game_service.storage.complete_session(session_id)
        # Get final game stats (in-memory only)
        # game_history = await game_service.storage.get_game_history(session_id)
        # Clear in-memory data
        await game_service.clear_session(session_id)
        return {
            "status": "success",
            "message": "Game session ended successfully",
            "game_history": None
        }
    except Exception as e:
        logger.error(f"Error ending game session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while ending the game session"
        )