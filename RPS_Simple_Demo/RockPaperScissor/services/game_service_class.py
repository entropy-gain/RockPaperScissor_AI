from typing import Dict, Any
from enum import Enum
from RockPaperScissor.models.adaptive_markov_ai import AdaptiveMarkovAI
from RockPaperScissor.models.base_ai import BaseAI
from RockPaperScissor.models.random_ai import RandomAI
from RockPaperScissor.game_cache.memory_cache import GameSessionCache
from RockPaperScissor.repositories.sql_storage import SQLStorage

class Move(Enum):
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"

class GameResult(Enum):
    PLAYER_WIN = "player_win"
    AI_WIN = "ai_win"
    DRAW = "draw"

class GameService:
    def __init__(self, storage=None, db_path: str = "data/game_history.db"):
        self.cache = GameSessionCache()
        self.model_states: Dict[str, Dict[str, Any]] = {}  # Track model state per session+ai
        self.ai_models = {
            "random": RandomAI(),
            "adaptive_markov": AdaptiveMarkovAI()
        }
        # Use provided storage or fallback to SQLStorage
        self.storage = storage or SQLStorage(db_path)

    async def initialize(self):
        await self.storage.initialize()

    async def play_round(self, session_id: str, player_move: str, ai_type: str = "random") -> Dict[str, Any]:
        try:
            # Get or initialize model state
            state_key = f"{session_id}__{ai_type}"
            model_state = self.model_states.get(state_key, None)
            
            # Update model state for adaptive_markov AI
            if ai_type == "adaptive_markov":
                if model_state is None:
                    model_state = None
                else:
                    model_state["player_second_last_move"] = model_state.get("player_last_move", None)
                    model_state["player_last_move"] = player_move
            
            # Get AI move
            ai = self.ai_models.get(ai_type, self.ai_models["random"])
            ai_move, updated_state = ai.make_move(model_state)
            self.model_states[state_key] = updated_state
            
            # Determine result
            result = self._determine_winner(player_move, ai_move)
            
            # Create game data for storage
            game_data = {
                'game_id': session_id,
                'player_move': player_move,
                'ai_move': ai_move,
                'result': result,
                'ai_type': ai_type,
                'ai_state': updated_state
            }
            
            # Save to storage
            await self.storage.save_game_round(game_data)
            
            # Update cache
            self.cache.update_session(session_id, game_data)
            
            # Get stats from cache
            session_data = self.cache.get_session(session_id)
            if not session_data:
                return {
                    "player_move": player_move,
                    "ai_move": ai_move,
                    "result": result,
                    "stats": self._get_empty_stats()
                }
                
            return {
                "player_move": player_move,
                "ai_move": ai_move,
                "result": result,
                "stats": self._get_formatted_stats(session_data)
            }
        except Exception as e:
            import traceback
            print(f"[GameService] Error in play_round: {e}\n{traceback.format_exc()}")
            return {"error": str(e)}

    async def save_session_to_db(self, session_id: str) -> bool:
        """Save the completed session and all rounds to storage"""
        session_data = self.cache.get_session(session_id)
        print(f"[DEBUG] save_session_to_db called for session_id: {session_id}")
        print(f"[DEBUG] session_data: {session_data}")
        if not session_data:
            print(f"[GameService] No session data found for session_id: {session_id}")
            return False
        try:
            success = await self.storage.save_full_session(session_id, session_data)
            if success:
                print(f"[GameService] Session {session_id} saved to storage.")
            else:
                print(f"[GameService] Failed to save session {session_id} to storage.")
            return success
        except Exception as e:
            import traceback
            print(f"[GameService] Error saving session to storage: {e}\n{traceback.format_exc()}")
            return False

    def _determine_winner(self, player_move: str, ai_move: str) -> str:
        if player_move == ai_move:
            return GameResult.DRAW.value
        winning_moves = {
            Move.ROCK.value: Move.SCISSORS.value,
            Move.PAPER.value: Move.ROCK.value,
            Move.SCISSORS.value: Move.PAPER.value
        }
        return GameResult.PLAYER_WIN.value if winning_moves[player_move] == ai_move else GameResult.AI_WIN.value

    def _get_empty_stats(self) -> Dict[str, Any]:
        return {
            "player_wins": 0,
            "ai_wins": 0,
            "draws": 0,
            "total_rounds": 0,
            "player_win_rate": "0.0%",
            "ai_win_rate": "0.0%",
            "rock_percent": "0%",
            "paper_percent": "0%",
            "scissors_percent": "0%"
        }

    def _get_formatted_stats(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        total = session_data['total_rounds']
        player_wins = session_data['player_wins']
        ai_wins = session_data['ai_wins']
        draws = session_data['draws']
        
        # Calculate win rates
        player_win_rate = (player_wins / total * 100) if total > 0 else 0
        ai_win_rate = (ai_wins / total * 100) if total > 0 else 0
        
        # Calculate player move distribution
        rounds = session_data['rounds']
        player_rock_count = sum(1 for r in rounds if r['player_move'] == Move.ROCK.value)
        player_paper_count = sum(1 for r in rounds if r['player_move'] == Move.PAPER.value)
        player_scissors_count = sum(1 for r in rounds if r['player_move'] == Move.SCISSORS.value)
        
        # Calculate AI move distribution
        ai_rock_count = sum(1 for r in rounds if r['ai_move'] == Move.ROCK.value)
        ai_paper_count = sum(1 for r in rounds if r['ai_move'] == Move.PAPER.value)
        ai_scissors_count = sum(1 for r in rounds if r['ai_move'] == Move.SCISSORS.value)
        
        total_moves = total
        player_rock_percent = (player_rock_count / total_moves * 100) if total_moves > 0 else 0
        player_paper_percent = (player_paper_count / total_moves * 100) if total_moves > 0 else 0
        player_scissors_percent = (player_scissors_count / total_moves * 100) if total_moves > 0 else 0
        
        ai_rock_percent = (ai_rock_count / total_moves * 100) if total_moves > 0 else 0
        ai_paper_percent = (ai_paper_count / total_moves * 100) if total_moves > 0 else 0
        ai_scissors_percent = (ai_scissors_count / total_moves * 100) if total_moves > 0 else 0
        
        return {
            "player_wins": player_wins,
            "ai_wins": ai_wins,
            "draws": draws,
            "total_rounds": total,
            "player_win_rate": f"{player_win_rate:.1f}%",
            "ai_win_rate": f"{ai_win_rate:.1f}%",
            "player_moves": {
                "rock": f"{player_rock_percent:.0f}%",
                "paper": f"{player_paper_percent:.0f}%",
                "scissors": f"{player_scissors_percent:.0f}%"
            },
            "ai_moves": {
                "rock": f"{ai_rock_percent:.0f}%",
                "paper": f"{ai_paper_percent:.0f}%",
                "scissors": f"{ai_scissors_percent:.0f}%"
            }
        }

    async def clear_session(self, session_id: str):
        # Remove only the specific session from cache
        self.cache.remove_session(session_id)
        # Clear model states
        keys_to_remove = [k for k in self.model_states if k.startswith(session_id)]
        for k in keys_to_remove:
            del self.model_states[k] 