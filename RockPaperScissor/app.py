from fastapi import FastAPI
from mangum import Mangum
from RockPaperScissor.routes.game import game_router
from RockPaperScissor.routes.history import history_router
from RockPaperScissor.routes.stats import stats_router

from fastapi.middleware.cors import CORSMiddleware


# Initialize FastAPI app
app = FastAPI()

# Include routers
app.include_router(game_router, prefix="/game", tags=["Game"])
app.include_router(history_router, prefix="/history", tags=["History"])
app.include_router(stats_router, prefix="/stats", tags=["Statistics"])



"""
for local testing only 
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (frontend access)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all request headers
)

# AWS Lambda handler
# handler = Mangum(app)