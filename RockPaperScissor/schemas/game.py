# RockPaperScissor/schemas/game.py
from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any
import uuid
from datetime import datetime

class GameRequest(BaseModel):
    """Schema for game requests"""
    user_id: Optional[str] = Field("test_user", description="Unique identifier of the user")
    session_id: Optional[str] = Field("test_session", description="Current game session ID")
    game_id: Optional[str] = Field(str(uuid.uuid4()), description="Unique identifier for specific game round")
    game_completed: bool = Field(False, description="Indicator if the game has completed")
    user_move: Optional[Literal["rock", "paper", "scissors"]] = Field(None, description="User's move")


class GameResponse(BaseModel):
    """Schema for game play response"""
    game_id: str = Field(..., description="Unique identifier of the game")
    user_id: str = Field(..., description="Unique identifier of the user")
    session_id: str = Field(..., description="Current game session ID")
    ai_move: str = Field(..., description="AI's move")
    result: Literal["player_win", "ai_win", "draw"] = Field(..., description="Game result")
    session_stats: Dict[str, Any] = Field(..., description="Session statistics")

class GameData(BaseModel):
    """Schema for internal game data storage"""
    game_id: str = Field(..., description="Unique identifier of the game")
    user_id: str = Field(..., description="Unique identifier of the user")
    session_id: str = Field(..., description="Current game session ID")
    timestamp: datetime = Field(default_factory=datetime.timestamp, description="Timestamp of the round")
    user_move: str = Field(..., description="User's move")
    ai_move: str = Field(..., description="AI's move")
    result: Literal["player_win", "ai_win", "draw"] = Field(..., description="Game result")
    session_stats: Dict[str, Any] = Field(..., description="Session statistics")
    model_name: str = Field(..., description="AI model name")
    model_state: Dict[str, Any] = Field({}, description="AI model state")

class LLMInteraction(BaseModel):
    """Schema for a single LLM interaction record."""
    prompt: str = Field(..., description="The prompt sent to the LLM")
    response: str = Field(..., description="The response received from the LLM")
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp(), 
                           description="Unix timestamp of the interaction")
    llm_model_name: str = Field(..., description="Name of the LLM model used")
    session_id: str = Field(..., description="Associated game session ID")
    game_id: str = Field(..., description="Associated game ID")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    metadata: Optional[dict] = Field(default_factory=dict, 
                                   description="Additional metadata about the interaction")

class LLMRequest(BaseModel):
    """Schema for LLM analysis requests"""
    user_id: str = Field(..., description="Unique identifier of the user")
    session_id: str = Field(..., description="Current game session ID")
    game_id: str = Field(..., description="Unique identifier for specific game round")
    analysis_type: Literal["game_state", "general"] = Field("game_state", description="Type of analysis requested")

