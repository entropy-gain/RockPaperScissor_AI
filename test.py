from RockPaperScissor.services import GameService
from RockPaperScissor.repositories.game_repository import GameRepository
from RockPaperScissor.schemas.game import GameRequest
import string
import random

# from RockPaperScissor.repositories.db import create_tables_if_not_exist

# create_tables_if_not_exist()


test = GameRequest(user_move="rock")

game_service = GameService()

print(game_service.play_round(test))


# session_id = "session_1744154886438_63"
# repo = GameRepository()

# result = repo.get_session_games(session_id = "session_1744154886438_63")
# print(0)
# print(result[0])
# print(1)
# print(result[1])