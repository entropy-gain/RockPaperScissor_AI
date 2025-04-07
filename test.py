from RockPaperScissor.services import GameService
from RockPaperScissor.repositories import GameRepository



game_service = GameService()
print(game_service.start_new_round(session_id = "666"))
print(game_service.play_round(game_id = "a9a13898-4072-4392-8256-0b9ab8cf6d13", player_move = "rock"))


