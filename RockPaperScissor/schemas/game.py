# RockPaperScissor/schemas/game.py
from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any
import uuid


class GameRequest(BaseModel):
    """Schema for game requests"""
    user_id: Optional[str] = Field("test_user", description="Unique identifier of the user")
    session_id: Optional[str] = Field("test_session", description="Current game session ID")
    game_id: Optional[str] = Field(str(uuid.uuid4()), description="Unique identifier for specific game round")
    user_move: Optional[Literal["rock", "paper", "scissors"]] = Field(None, description="User's move")
    ai_type: Optional[Literal["random", "pattern", "markov", "adaptive_markov"]] = Field("adaptive_markov", description="Type of AI to play against")

    class Config:
        extra = "allow"


class GameResponse(BaseModel):
    """Schema for game play response"""
    game_id: str = Field(..., description="Unique identifier of the game")
    user_id: str = Field(..., description="Unique identifier of the user")
    session_id: str = Field(..., description="Current game session ID")
    user_move: str = Field(..., description="User's move")
    ai_move: str = Field(..., description="AI's move")
    ai_type: str = Field(..., description="Type of AI used in this game")
    result: Literal["player_win", "ai_win", "draw"] = Field(..., description="Game result")
    session_stats: Dict[str, Any] = Field(..., description="Session statistics")    
    class Config:
        json_schema_extra = {
            "example": {
                "game_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user123",
                "session_id": "session456",
                "user_move": "rock",
                "ai_move": "scissors",
                "ai_type": "adaptive_markov",
                "result": "player_win",
                "model_state": {"player_last_move": "rock", "patterns": {"rock": 0.4, "paper": 0.3, "scissors": 0.3}},
                "session_stats": {
                    "total_games": 10,
                    "player_wins": 5,
                    "ai_wins": 3,
                    "draws": 2,
                    "rock_count": 4,
                    "paper_count": 3,
                    "scissors_count": 3,
                    "player_win_rate": 50.0,
                    "ai_win_rate": 30.0
                }
            }
        }

class GameData(BaseModel):
    """Schema for internal game data storage"""
    game_id: str = Field(..., description="Unique identifier of the game")
    user_id: str = Field(..., description="Unique identifier of the user")
    session_id: str = Field(..., description="Current game session ID")
    user_move: str = Field(..., description="User's move")
    ai_move: str = Field(..., description="AI's move")
    ai_type: str = Field(..., description="Type of AI used in this game")
    result: Literal["player_win", "ai_win", "draw"] = Field(..., description="Game result")
    model_state: Dict[str, Any] = Field({}, description="AI model state")
    session_stats: Dict[str, Any] = Field(..., description="Session statistics")

class AIPerformance(BaseModel):
    """Schema for AI performance stats"""
    name: str = Field(..., description="Name of the AI model")
    ai_win_rate: float = Field(..., description="AI's win rate as percentage")
    player_win_rate: float = Field(..., description="Player's win rate against this AI")
    ai_wins: int = Field(..., description="Number of rounds won by AI")
    player_wins: int = Field(..., description="Number of rounds won by players")
    draws: int = Field(..., description="Number of rounds drawn")
    total_games: int = Field(..., description="Total number of rounds played")

