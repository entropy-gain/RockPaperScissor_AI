"""
Main application module for RockPaperScissor game.
Sets up the FastAPI application and routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from RockPaperScissor.routes import game_router
from RockPaperScissor.utils.logging import setup_logging
from RockPaperScissor.game_cache.memory_cache import GameSessionCache, LLMCache
from RockPaperScissor.repositories import Storage
from RockPaperScissor.services import GameService, LLMService
from RockPaperScissor.repositories.sql_storage import SQLStorage

# Setup logging
logger = setup_logging()

# Global variables for service instances
game_service = None
storage = None
llm_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run on application startup and shutdown"""
    global game_service, storage, llm_service
    
    logger.info("Application starting up")
    
    # Initialize storage and services
    storage = SQLStorage()
    await storage.initialize()  # This will create tables if they don't exist
    llm_service = LLMService(storage=storage)
    game_service = GameService(storage=storage)
    
    logger.info("Application initialized successfully")
    
    yield 
    
    # Cleanup on shutdown
    logger.info("Application shutting down")
    if game_service:
        await game_service.shutdown()
    if llm_service:
        await llm_service.shutdown()
    if storage:
        await storage.close()

# Create FastAPI app
app = FastAPI(
    title="Rock Paper Scissors Game API",
    description="API for the Rock Paper Scissors game featuring various AI opponents",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(game_router, prefix="/game", tags=["game"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint to verify API is running"""
    return {
        "message": "Rock Paper Scissors Game API",
        "status": "online",
        "version": "1.0.0"
    }

# Run application (development only)
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting development server")
    uvicorn.run(app, host="0.0.0.0", port=8000)