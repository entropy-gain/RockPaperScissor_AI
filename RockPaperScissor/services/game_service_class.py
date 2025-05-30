from typing import Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from RockPaperScissor.models.adaptive_markov_ai import AdaptiveMarkovAI

class Move(Enum):
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"

class GameResult(Enum):
    PLAYER_WIN = "player_win"
    AI_WIN = "ai_win"
    DRAW = "draw"

@dataclass
class GameStats:
    player_wins: int = 0
    ai_wins: int = 0
    draws: int = 0
    total_rounds: int = 0
    rock_count: int = 0
    paper_count: int = 0
    scissors_count: int = 0

class BaseAI:
    def make_move(self, model_state: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        raise NotImplementedError

class RandomAI(BaseAI):
    def make_move(self, model_state: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        import random
        move = random.choice([Move.ROCK.value, Move.PAPER.value, Move.SCISSORS.value])
        return move, {}

class GameService:
    def __init__(self):
        self.stats: Dict[str, GameStats] = {}
        self.model_states: Dict[str, Dict[str, Any]] = {}  # Track model state per session+ai
        self.ai_models = {
            "random": RandomAI(),
            "adaptive_markov": AdaptiveMarkovAI()
        }

    async def initialize(self):
        pass

    async def play_round(self, session_id: str, player_move: str, ai_type: str = "random") -> Dict[str, Any]:
        if session_id not in self.stats:
            self.stats[session_id] = GameStats()
        state_key = f"{session_id}__{ai_type}"
        model_state = self.model_states.get(state_key, None)
        if ai_type == "adaptive_markov":
            if model_state is None:
                model_state = None
            else:
                model_state["player_second_last_move"] = model_state.get("player_last_move", None)
                model_state["player_last_move"] = player_move
        ai = self.ai_models.get(ai_type, self.ai_models["random"])
        ai_move, updated_state = ai.make_move(model_state)
        self.model_states[state_key] = updated_state
        result = self._determine_winner(player_move, ai_move)
        stats = self.stats[session_id]
        stats.total_rounds += 1
        if result == GameResult.PLAYER_WIN.value:
            stats.player_wins += 1
        elif result == GameResult.AI_WIN.value:
            stats.ai_wins += 1
        else:
            stats.draws += 1
        if player_move == Move.ROCK.value:
            stats.rock_count += 1
        elif player_move == Move.PAPER.value:
            stats.paper_count += 1
        else:
            stats.scissors_count += 1
        return {
            "player_move": player_move,
            "ai_move": ai_move,
            "result": result,
            "stats": self._get_formatted_stats(session_id)
        }

    def _determine_winner(self, player_move: str, ai_move: str) -> str:
        if player_move == ai_move:
            return GameResult.DRAW.value
        winning_moves = {
            Move.ROCK.value: Move.SCISSORS.value,
            Move.PAPER.value: Move.ROCK.value,
            Move.SCISSORS.value: Move.PAPER.value
        }
        return GameResult.PLAYER_WIN.value if winning_moves[player_move] == ai_move else GameResult.AI_WIN.value

    def _get_formatted_stats(self, session_id: str) -> Dict[str, Any]:
        stats = self.stats[session_id]
        total = stats.total_rounds
        player_wins = stats.player_wins
        ai_wins = stats.ai_wins
        draws = stats.draws
        player_win_rate = (player_wins / total * 100) if total > 0 else 0
        ai_win_rate = (ai_wins / total * 100) if total > 0 else 0
        total_moves = stats.rock_count + stats.paper_count + stats.scissors_count
        rock_percent = (stats.rock_count / total_moves * 100) if total_moves > 0 else 0
        paper_percent = (stats.paper_count / total_moves * 100) if total_moves > 0 else 0
        scissors_percent = (stats.scissors_count / total_moves * 100) if total_moves > 0 else 0
        return {
            "player_wins": player_wins,
            "ai_wins": ai_wins,
            "draws": draws,
            "total_rounds": total,
            "player_win_rate": f"{player_win_rate:.1f}%",
            "ai_win_rate": f"{ai_win_rate:.1f}%",
            "rock_percent": f"{rock_percent:.0f}%",
            "paper_percent": f"{paper_percent:.0f}%",
            "scissors_percent": f"{scissors_percent:.0f}%"
        }

    async def clear_session(self, session_id: str):
        if session_id in self.stats:
            del self.stats[session_id]
        keys_to_remove = [k for k in self.model_states if k.startswith(session_id)]
        for k in keys_to_remove:
            del self.model_states[k] 