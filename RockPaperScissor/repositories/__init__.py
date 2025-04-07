"""
Repository package initialization for RockPaperScissor game.
"""
from .game_repository import GameRepository
from .db import get_dynamodb_resource, get_dynamodb_client, create_tables_if_not_exist

__all__ = [
    'GameRepository',
    'get_dynamodb_resource',
    'get_dynamodb_client',
    'create_tables_if_not_exist'
]