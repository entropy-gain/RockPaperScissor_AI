"""
Routes package initialization for RockPaperScissor game.
Contains API routes definitions.
"""
from .game import game_router
from .stats import stats_router

__all__ = [
    'game_router',
    'stats_router'
]