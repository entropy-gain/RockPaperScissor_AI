import random
from .base_ai import BaseAI

class RandomAI(BaseAI):
    def make_move(self, history):
        return random.choice(["rock", "paper", "scissors"])
