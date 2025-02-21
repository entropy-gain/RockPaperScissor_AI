from .base_ai import BaseAI

class PatternAI(BaseAI):
    def make_move(self, history):
        if not history:
            return "rock"
        most_common = max(history, key = history.get)
        return self.counter_move(most_common)
    
    def counter_move(self, move):
        counter_map = {"rock": "paper", "paper": "scissors", "scissors": "rock"}
        return counter_map[move]
    