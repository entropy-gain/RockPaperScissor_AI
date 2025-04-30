"""
LLM service for game analysis and summaries.
"""
from typing import Dict, Any, Optional
from ..game_cache import LLMCache, GameSessionCache
from ..utils import setup_logging
from ..repositories import Storage
from ..schemas.game import LLMRequest, LLMInteraction

logger = setup_logging()

class LLMService:
    """Service for LLM-related operations."""
    
    def __init__(self, storage: Storage):
        """Initialize the LLM service with storage."""
        self.llm_cache = LLMCache(storage=storage)
        self.game_cache = GameSessionCache(storage=storage)
        logger.info("LLM service initialized")

    def analyze_game_state(self, llm_request: LLMRequest) -> str:
        """
        Get LLM analysis of the current game state.
        
        Args:
            llm_request: LLMRequest object containing analysis request information
            
        Returns:
            str: LLM's analysis of the game
        """
        # Get the latest game state from cache
        latest_record = self.game_cache.get_latest_record(llm_request.session_id)
        
        if not latest_record and llm_request.analysis_type == "game_state":
            # If no game state found and specific analysis requested, return general analysis
            response = "No game data available for analysis. This is a general analysis of the game."
        else:
            # TODO: Implement actual LLM call
            # For now, return a placeholder response
            if llm_request.analysis_type == "game_state":
                response = "This is a placeholder LLM response for game state analysis."
            else:
                response = "This is a placeholder LLM response for general analysis."
        
        # Create LLMInteraction record
        interaction = LLMInteraction(
            prompt="Analyze current game state",
            response=response,
            llm_model_name="gpt-3.5-turbo",  # TODO: Make this configurable
            session_id=llm_request.session_id,
            game_id=llm_request.game_id,
            user_id=llm_request.user_id,
            metadata={"type": "game_analysis", "analysis_type": llm_request.analysis_type}
        )
        
        # Log the interaction
        self.llm_cache.add_interaction(interaction)
        
        return response

    def summarize_game_session(self, model_state: Dict[str, Any]) -> str:
        """
        Get LLM summary of the game session.
        
        Args:
            model_state: Final state of the game model
            
        Returns:
            str: LLM's summary of the game session
        """
        # TODO: Implement actual LLM call
        # For now, return a placeholder response
        response = "This is a placeholder LLM response for game summary."
        
        # Create LLMInteraction record
        interaction = LLMInteraction(
            prompt="Summarize game session",
            response=response,
            llm_model_name="gpt-3.5-turbo",  # TODO: Make this configurable
            session_id=model_state.get("session_id", "unknown"),
            game_id=model_state.get("game_id", "unknown"),
            user_id=model_state.get("user_id", "unknown"),
            metadata={"type": "game_summary"}
        )
        
        # Log the interaction
        self.llm_cache.add_interaction(interaction)
        
        return response

    async def shutdown(self):
        """Gracefully shutdown the LLM service."""
        await self.llm_cache.shutdown()
        logger.info("LLM service shutdown complete")
