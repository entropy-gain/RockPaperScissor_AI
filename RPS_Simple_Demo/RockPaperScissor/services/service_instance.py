from RockPaperScissor.services.game_service_class import GameService
from RockPaperScissor.repositories import CombinedStorage

# Initialize storage with both SQLite and S3
storage = CombinedStorage()
game_service = GameService(storage=storage) 