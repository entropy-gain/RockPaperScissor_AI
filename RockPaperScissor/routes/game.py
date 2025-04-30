# backend/routes/game.py
from fastapi import APIRouter, HTTPException, Request
from RockPaperScissor.services import GameService, LLMService
from RockPaperScissor.schemas.game import GameRequest, GameResponse, GameSummary, LLMRequest
from RockPaperScissor.utils.logging import setup_logging
from RockPaperScissor.repositories import Storage

# Set up logger
logger = setup_logging()

game_router = APIRouter()

# Initialize services
storage = Storage()
game_service = GameService(storage=storage)
llm_service = LLMService(storage)
    
@game_router.post("/play")
async def play_round(request: Request, game_request: GameRequest):
    """
    Play a round with the player's move.
    """
    try:
        # Log the request
        logger.info(f"Play round request: {game_request.model_dump()}")

        # Get IP Address for future use
        ip_address = request.client.host
        logger.debug(f"Request from IP: {ip_address}")

        # Call service method to play the round
        result = game_service.play_round(game_request)
        return result
    
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

@game_router.post("/analyze")
async def analyze_game_state(llm_request: LLMRequest):
    """
    Get LLM analysis of the current game state.
    """
    try:
        # Log the request
        logger.info(f"Analyze request: {llm_request.model_dump()}")
        
        # Get LLM analysis directly from LLM service
        analysis = llm_service.analyze_game_state(llm_request)
        return {"analysis": analysis}
        
    except Exception as e:
        logger.error(f"Error analyzing game state: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while analyzing the game state"
        )

@game_router.post("/end")
async def end_game(game_request: GameRequest):
    """
    End the current game session and get a summary.
    """
    try:
        summary = game_service.end_game(game_request)
        return summary
    except Exception as e:
        logger.error(f"Error ending game: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while ending the game"
        )