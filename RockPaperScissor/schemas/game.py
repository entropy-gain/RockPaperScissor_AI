# RockPaperScissor/schemas/game.py
from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any

class GameRequest(BaseModel):
    """Schema for game requests"""
    user_id: Optional[str] = Field(None, description="Unique identifier of the user")
    session_id: Optional[str] = Field(None, description="Current game session ID")
    game_id: Optional[str] = Field(None, description="Unique identifier for specific game round")
    user_move: Optional[Literal["rock", "paper", "scissors"]] = Field(None, description="User's move")
    ai_type: Optional[Literal["random", "pattern", "markov", "adaptive_markov"]] = Field("adaptive_markov", description="Type of AI to play against")

    class Config:
        # 允许额外字段，使API更灵活
        extra = "allow"

class GameResponse(BaseModel):
    """Schema for game play response"""
    game_id: str = Field(..., description="Unique identifier of the game")
    session_id: str = Field(..., description="Current game session ID")
    user_move: str = Field(..., description="User's move")
    ai_move: str = Field(..., description="AI's move")
    result: Literal["player_win", "ai_win", "draw"] = Field(..., description="Game result")
    session_stats: Optional[Dict[str, Any]] = Field(None, description="Session statistics")

class NewGameResponse(BaseModel):
    """Schema for new game response"""
    game_id: str = Field(..., description="Unique identifier for the new game round")
    session_id: str = Field(..., description="Session identifier")

class AIPerformance(BaseModel):
    """Schema for AI performance stats"""
    name: str = Field(..., description="Name of the AI model")
    ai_win_rate: float = Field(..., description="AI's win rate as percentage")
    player_win_rate: float = Field(..., description="Player's win rate against this AI")
    ai_wins: int = Field(..., description="Number of rounds won by AI")
    player_wins: int = Field(..., description="Number of rounds won by players")
    draws: int = Field(..., description="Number of rounds drawn")
    total_rounds: int = Field(..., description="Total number of rounds played")

class SessionStats(BaseModel):
    """Schema for session statistics"""
    total_rounds: int = Field(..., description="Total number of rounds played")
    player_wins: int = Field(..., description="Number of rounds won by player")
    ai_wins: int = Field(..., description="Number of rounds won by AI")
    draws: int = Field(..., description="Number of rounds drawn")
    player_win_rate: float = Field(..., description="Player's win rate as percentage")
    ai_win_rate: float = Field(..., description="AI's win rate as percentage")
    ai_type: Optional[str] = Field(None, description="Type of AI used in this session")
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")