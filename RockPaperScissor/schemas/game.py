from pydantic import BaseModel

class GameRequest(BaseModel):
    user_id: str
    user_move: str
    ai_type: str

class GameResponse(BaseModel):
    user_move: str
    ai_move: str
    result: str