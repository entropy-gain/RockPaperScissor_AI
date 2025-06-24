# RockPaperScissor/schemas/game.py
from pydantic import BaseModel, Field 
# from typing import Optional, Dict, Any, Literal # OLD - Pydantic might not re-export Literal
from typing import Optional, Dict, Any, Literal # NEW - Import directly from typing

import uuid
from datetime import datetime

class GameRequest(BaseModel):
    user_id: Optional[str] = Field("test_user")
    session_id: Optional[str] = Field("test_session")
    game_id: str = Field(default_factory=lambda: "gr_game_" + str(uuid.uuid4()))
    user_move: Optional[Literal["rock", "paper", "scissors"]] = None # Literal is used here
    ai_type: Optional[str] = None

class GameResponse(BaseModel):
    game_id: str
    user_id: str
    session_id: str
    user_move: str
    ai_move: str
    result: Literal["player_win", "ai_win", "draw"] # Literal is used here
    session_stats: Dict[str, Any]