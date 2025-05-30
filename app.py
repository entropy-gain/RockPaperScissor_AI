# RPS_SIMPLE_DEMO/app.py
import gradio as gr
import uuid
import asyncio
from typing import Dict, Any, Tuple, List, Optional
from dataclasses import dataclass
from enum import Enum
from RockPaperScissor.models.adaptive_markov_ai import AdaptiveMarkovAI
#from RockPaperScissor.repositories import CombinedStorage

# FastAPI imports
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from RockPaperScissor.routes import game_router
from RockPaperScissor.services.service_instance import game_service

# --- Game Constants and Types ---
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

# --- AI Models ---
class BaseAI:
    def make_move(self, model_state: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        raise NotImplementedError

class RandomAI(BaseAI):
    def make_move(self, model_state: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        import random
        move = random.choice([Move.ROCK.value, Move.PAPER.value, Move.SCISSORS.value])
        return move, {}

# --- Game Service ---
class GameService:
    def __init__(self):
        # self.storage = CombinedStorage()  # Persistent storage (commented for Hugging Face)
        self.stats: Dict[str, GameStats] = {}
        self.model_states: Dict[str, Dict[str, Any]] = {}  # Track model state per session+ai
        self.ai_models = {
            "random": RandomAI(),
            "adaptive_markov": AdaptiveMarkovAI()
        }

    async def initialize(self):
        # await self.storage.initialize()  # Persistent storage (commented for Hugging Face)
        pass

    async def play_round(self, session_id: str, player_move: str, ai_type: str = "random") -> Dict[str, Any]:
        # Initialize stats for new session
        if session_id not in self.stats:
            self.stats[session_id] = GameStats()
        # Track model state per session+ai
        state_key = f"{session_id}__{ai_type}"
        model_state = self.model_states.get(state_key, None)
        # --- Markov memory update: update state BEFORE calling make_move ---
        if ai_type == "adaptive_markov":
            if model_state is None:
                model_state = None  # Will be initialized in make_move
            else:
                # Shift memory: second_last <- last, last <- current
                model_state["player_second_last_move"] = model_state.get("player_last_move", None)
                model_state["player_last_move"] = player_move
        # Get AI move
        ai = self.ai_models.get(ai_type, self.ai_models["random"])
        ai_move, updated_state = ai.make_move(model_state)
        self.model_states[state_key] = updated_state
        # Determine result
        result = self._determine_winner(player_move, ai_move)
        # Update stats
        stats = self.stats[session_id]
        stats.total_rounds += 1
        if result == GameResult.PLAYER_WIN.value:
            stats.player_wins += 1
        elif result == GameResult.AI_WIN.value:
            stats.ai_wins += 1
        else:
            stats.draws += 1
        # Update move counts
        if player_move == Move.ROCK.value:
            stats.rock_count += 1
        elif player_move == Move.PAPER.value:
            stats.paper_count += 1
        else:
            stats.scissors_count += 1

        # Save to storage (commented for Hugging Face)
        # game_data = {
        #     'game_id': session_id,
        #     'player_move': player_move,
        #     'ai_move': ai_move,
        #     'result': result,
        #     'ai_type': ai_type,
        #     'ai_state': updated_state
        # }
        # await self.storage.save_game_round(game_data)

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

        # Calculate percentages
        player_win_rate = (player_wins / total * 100) if total > 0 else 0
        ai_win_rate = (ai_wins / total * 100) if total > 0 else 0

        # Calculate move percentages
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
        """Clear session data from memory"""
        if session_id in self.stats:
            del self.stats[session_id]
        keys_to_remove = [k for k in self.model_states if k.startswith(session_id)]
        for k in keys_to_remove:
            del self.model_states[k]

# --- Gradio Interface ---
class RockPaperScissorsUI:
    def __init__(self, game_service: GameService):
        self.game_service = game_service
        self.session_id = None  # Will be set from State
        self.ai_models = list(self.game_service.ai_models.keys())
        self.ai_descriptions = {
            "random": "Random AI: Makes completely random moves.",
            "adaptive_markov": "Adaptive Markov AI: Uses entropy-weighted Markov and frequency models to predict your next move."
        }
        self.last_move = None

    async def reset_session(self, session_id: str):
        await self.game_service.clear_session(session_id)
        return {"status": "ok"}

    def create_interface(self):
        with gr.Blocks(theme=gr.themes.Soft(), title="Rock Paper Scissors 🎮") as demo:
            gr.Markdown("# 🪨📄✂️ Rock Paper Scissors")
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🎮 Game Setup")
                    ai_dropdown = gr.Dropdown(
                        choices=self.ai_models,
                        value=self.ai_models[0],
                        label="Select AI Opponent"
                    )
                    ai_description = gr.Markdown(self.ai_descriptions[self.ai_models[0]])
                    
                    with gr.Row():
                        rock_btn = gr.Button("🪨 Rock", variant="secondary", elem_classes=["move-btn"])
                        paper_btn = gr.Button("📄 Paper", variant="secondary", elem_classes=["move-btn"])
                        scissors_btn = gr.Button("✂️ Scissors", variant="secondary", elem_classes=["move-btn"])

                with gr.Column(scale=2):
                    gr.Markdown("### 📊 Game Statistics")
                    stats_display = gr.Markdown()
                    result_display = gr.Markdown("Make your move!")

            ai_dropdown.change(
                fn=self.update_ai_description,
                inputs=[ai_dropdown],
                outputs=[ai_description]
            )

            # Use a Gradio State to store the session ID
            move_state = gr.State("")
            session_id_state = gr.State("")

            async def play_rock(ai_type, session_id):
                if not session_id:
                    session_id = f"session_{uuid.uuid4()}"
                self.session_id = session_id
                stats, result = await self.play_round(ai_type, "rock")
                return stats, result, session_id
            async def play_paper(ai_type, session_id):
                if not session_id:
                    session_id = f"session_{uuid.uuid4()}"
                self.session_id = session_id
                stats, result = await self.play_round(ai_type, "paper")
                return stats, result, session_id
            async def play_scissors(ai_type, session_id):
                if not session_id:
                    session_id = f"session_{uuid.uuid4()}"
                self.session_id = session_id
                stats, result = await self.play_round(ai_type, "scissors")
                return stats, result, session_id

            rock_btn.click(
                fn=play_rock,
                inputs=[ai_dropdown, session_id_state],
                outputs=[stats_display, result_display, session_id_state]
            )
            paper_btn.click(
                fn=play_paper,
                inputs=[ai_dropdown, session_id_state],
                outputs=[stats_display, result_display, session_id_state]
            )
            scissors_btn.click(
                fn=play_scissors,
                inputs=[ai_dropdown, session_id_state],
                outputs=[stats_display, result_display, session_id_state]
            )

        return demo

    def update_ai_description(self, ai_type: str) -> str:
        return self.ai_descriptions[ai_type]

    async def play_round(self, ai_type: str, move: str) -> Tuple[str, str]:
        # Ensure self.session_id is used, which should be set by play_action
        if not self.session_id: 
             # This should ideally not be hit if play_action sets it
            return "Internal Error: Session ID missing in play_round.", "Error"
        result = await self.game_service.play_round(self.session_id, move, ai_type)
        stats = result["stats"]
        stats_text = f"""
        ### Game Statistics
        - Total Rounds: {stats['total_rounds']}
        - Player Wins: {stats['player_wins']} ({stats['player_win_rate']})
        - AI Wins: {stats['ai_wins']} ({stats['ai_win_rate']})
        - Draws: {stats['draws']}

        ### Move Distribution
        - Rock: {stats['rock_percent']}
        - Paper: {stats['paper_percent']}
        - Scissors: {stats['scissors_percent']}
        """
        result_text = f"""
        ### Round Result
        You played: {result['player_move'].upper()}
        AI played: {result['ai_move'].upper()}
        Result: {result['result'].replace('_', ' ').title()}
        """
        return stats_text, result_text

    async def clear_session(self, session_id: str): # Make sure this is async if game_service.clear_session is
        await self.game_service.clear_session(session_id)
        return {"status": "ok"}

# Create FastAPI app
app = FastAPI()

# Create Gradio interface
ui = RockPaperScissorsUI(game_service)
demo = ui.create_interface()

# Mount Gradio app
app = gr.mount_gradio_app(app, demo, path="/")

# Add game routes
app.include_router(game_router, prefix="/game")

# Initialize the app
@app.on_event("startup")
async def startup_event():
    await game_service.initialize()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)