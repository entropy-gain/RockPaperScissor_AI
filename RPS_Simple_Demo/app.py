import gradio as gr
import uuid
import httpx
import os

# FastAPI imports
from fastapi import FastAPI, Request, Body
from fastapi.responses import RedirectResponse
from RockPaperScissor.routes import game_router
from RockPaperScissor.services.service_instance import game_service
from RockPaperScissor.services.LLM_service import LLMService

# Create FastAPI app
app = FastAPI()

# Create LLM service instance
llm_service = LLMService()

# Import spaces after the GPU function is defined
try:
    import spaces
    from spaces import GPU
    print("[APP] spaces.GPU imported successfully")
except ImportError:
    print("[APP] spaces.GPU not available")
    def GPU(f):
        return f

# Initialize storage on startup
@app.on_event("startup")
async def startup_event():
    await game_service.initialize()

# --- Game Constants and Types ---
from enum import Enum

class Move(Enum):
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"

class GameResult(Enum):
    PLAYER_WIN = "player_win"
    AI_WIN = "ai_win"
    DRAW = "draw"

# --- Gradio Interface ---
class RockPaperScissorsUI:
    def __init__(self, game_service):
        self.game_service = game_service
        self.session_id = None  # Will be set from State
        self.ai_models = list(self.game_service.ai_models.keys())
        self.ai_descriptions = {
            "random": "Random AI: Makes completely random moves.",
            "adaptive_markov": "Adaptive Markov AI: Uses entropy-weighted Markov and frequency models to predict your next move."
        }
        self.last_move = None

    def update_ai_description(self, ai_type):
        """Update the AI description when the AI type is changed."""
        return self.ai_descriptions.get(ai_type, "Unknown AI type")

    async def play_round(self, ai_type: str, player_move: str):
        """Play a round of the game."""
        if not self.session_id:
            self.session_id = f"session_{uuid.uuid4()}"
        
        # Play the round using the game service
        result = await self.game_service.play_round(self.session_id, player_move, ai_type)
        
        if "error" in result:
            return "<div style='color:red;'>Error: " + result["error"] + "</div>", "Error occurred during the game."
        
        # Format the stats and result for display (HTML card)
        stats = result.get("stats", {})
        self.latest_stats = stats  # Store latest stats for help
        stats_html = f'''
<div style="background:#23243a;padding:20px;border-radius:16px;box-shadow:0 2px 8px #0002;max-width:420px;">
  <h4 style="margin-top:0;">📊 Game Statistics</h4>
  <b>Summary</b><br>
  <ul style="margin:0 0 10px 0;padding-left:18px;">
    <li><b>Total Rounds:</b> {stats.get('total_rounds', 0)}</li>
    <li>🧑 <b>Player Wins:</b> {stats.get('player_wins', 0)} ({stats.get('player_win_rate', '0.0%')})</li>
    <li>🤖 <b>AI Wins:</b> {stats.get('ai_wins', 0)} ({stats.get('ai_win_rate', '0.0%')})</li>
    <li>🤝 <b>Draws:</b> {stats.get('draws', 0)}</li>
  </ul>
  <b>Player Move Distribution</b>
  <ul style="margin:0 0 10px 0;padding-left:18px;">
    <li>🪨 Rock: {stats.get('player_moves', {}).get('rock', '0%')}</li>
    <li>📄 Paper: {stats.get('player_moves', {}).get('paper', '0%')}</li>
    <li>✂️ Scissors: {stats.get('player_moves', {}).get('scissors', '0%')}</li>
  </ul>
  <b>AI Move Distribution</b>
  <ul style="margin:0 0 10px 0;padding-left:18px;">
    <li>🪨 Rock: {stats.get('ai_moves', {}).get('rock', '0%')}</li>
    <li>📄 Paper: {stats.get('ai_moves', {}).get('paper', '0%')}</li>
    <li>✂️ Scissors: {stats.get('ai_moves', {}).get('scissors', '0%')}</li>
  </ul>
</div>
'''
        
        # Format the result message
        result_text = f"""
**Last Round**
- You played: **{player_move.capitalize()}**
- AI played: **{result['ai_move'].capitalize()}**
- **Result:** _{result['result'].replace('_', ' ').title()}_
"""
        
        return stats_html, result_text

    async def get_help(self, session_id: str):
        """Get help from the LLM service using the latest stats."""
        try:
            stats = getattr(self, 'latest_stats', None)
            response = await llm_service.generate_response("", stats)
            return response
        except Exception as e:
            print(f"Error getting help: {str(e)}")
            return "Sorry, I'm having trouble analyzing the game right now."

    async def reset_session(self, session_id: str):
        # Use environment variable for base URL, fallback to localhost
        base_url = os.getenv("HF_SPACE_URL", "http://localhost:7860")
        print(f"[DEBUG] HF_SPACE_URL: {base_url}")
        # Remove trailing slash if present to avoid double slashes
        if not base_url or base_url == "/":
            base_url = "http://localhost:7860"
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        url = f"{base_url}/api/game/end"
        print(f"[DEBUG] Final endgame URL: {url}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"session_id": session_id}
            )
            print("[DEBUG] /api/game/end response:", response.text)
        # Optionally, also clear the session in-memory (if needed)
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
                    # Add End Game button
                    end_btn = gr.Button("End Game", variant="stop", elem_id="end-game-btn")
                    # Add Help button
                    help_btn = gr.Button("💡 Get Help", variant="primary", elem_id="help-btn")
                    # Add a dedicated box for the help answer, initially empty
                    help_answer_box = gr.Markdown("", visible=True)

                with gr.Column(scale=2):
                    gr.Markdown("### 📊 Game Statistics")
                    with gr.Group():
                        stats_display = gr.HTML("<div id='stats-box'></div>")
                    result_display = gr.Markdown("Make your move!")
                    end_result_display = gr.Markdown(visible=False)
                    status_display = gr.Markdown(visible=True)

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

            # Add a hidden HTML block with JS to auto-save on tab close
            gr.HTML("""
    <script>
    // Store session ID in localStorage whenever it changes
    window.setRpsSessionId = function(session_id) {
        if (session_id) {
            localStorage.setItem('rps_session_id', session_id);
        }
    };
    // On tab close, send session end to backend
    window.onbeforeunload = function() {
        let session_id = localStorage.getItem('rps_session_id');
        if (session_id) {
            navigator.sendBeacon("/game/end", JSON.stringify({session_id: session_id}));
        }
    };
    </script>
    """)

            # Inject JS to click End Game button on tab close
            gr.HTML("""
<script>
window.onbeforeunload = function() {
    var btn = document.getElementById('end-game-btn');
    if (btn) {
        btn.click();
    }
};
</script>
""")

            # After each move, update localStorage with the session ID
            def update_session_id_js(session_id):
                return f"window.setRpsSessionId('{session_id}');"

            rock_btn.click(
                fn=play_rock,
                inputs=[ai_dropdown, session_id_state],
                outputs=[stats_display, result_display, session_id_state],
                js=update_session_id_js
            )
            paper_btn.click(
                fn=play_paper,
                inputs=[ai_dropdown, session_id_state],
                outputs=[stats_display, result_display, session_id_state],
                js=update_session_id_js
            )
            scissors_btn.click(
                fn=play_scissors,
                inputs=[ai_dropdown, session_id_state],
                outputs=[stats_display, result_display, session_id_state],
                js=update_session_id_js
            )

            # End Game button logic
            async def end_game(session_id):
                if not session_id:
                    return "No session to end. Play a round first!"
                result = await self.reset_session(session_id)
                return f"End Game: {result['status']} - {result.get('message', '')}"

            end_btn.click(
                fn=end_game,
                inputs=[session_id_state],
                outputs=[end_result_display],
            )
            end_result_display.visible = True

            # Help button logic
            async def get_help_callback(session_id):
                response = await self.get_help(session_id)
                print(f"[DEBUG] LLM Help Response: {response}")
                return response

            help_btn.click(
                fn=get_help_callback,
                inputs=[session_id_state],
                outputs=[help_answer_box]
            )

        return demo

# Create UI instance and mount it to FastAPI
demo = RockPaperScissorsUI(game_service).create_interface()
app = gr.mount_gradio_app(app, demo, path="/gradio")

# Add help endpoint
@app.post("/api/help")
async def get_help(request: Request, body: dict = Body(...)):
    try:
        session_id = body.get("session_id")
        stats = None
        if session_id:
            # Try to get stats from the game service
            session_data = game_service.cache.get_session(session_id)
            if session_data:
                # Calculate AI move distribution
                ai_moves = [round['ai_move'] for round in session_data['rounds']]
                total_moves = len(ai_moves)
                if total_moves > 0:
                    move_distribution = {
                        "rock": ai_moves.count("rock"),
                        "paper": ai_moves.count("paper"),
                        "scissors": ai_moves.count("scissors")
                    }
                    stats = {"move_distribution": move_distribution}
        
        # Generate response using LLM service
        response = await llm_service.generate_response("", stats)
        return {"suggestion": response}
        
    except Exception as e:
        print(f"Error getting help: {str(e)}")
        return {"suggestion": "Sorry, I'm having trouble analyzing the game right now."}

# Include game router
app.include_router(game_router, prefix="/api/game")

# Initialize the app
if __name__ == "__main__":
    import uvicorn
    print("\n[INFO] Open your browser and go to: http://localhost:7860/gradio to use the Rock Paper Scissors app!\n")
    uvicorn.run(app, host="0.0.0.0", port=7860)