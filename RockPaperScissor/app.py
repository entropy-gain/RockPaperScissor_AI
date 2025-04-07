"""
Main application module for RockPaperScissor game.
Sets up the FastAPI application and routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from RockPaperScissor.routes import game_router
from RockPaperScissor.repositories.db import create_tables_if_not_exist
from RockPaperScissor.utils.logging import setup_logging

# Setup logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run on application startup"""
    logger.info("Application starting up")
    
     # Ensure DB tables exist
    create_tables_if_not_exist()
    logger.info("Database tables verified")
    
    yield 
    
    logger.info("Application shutting down")

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

# Lambda handler for AWS deployment
def lambda_handler(event, context):
    """
    AWS Lambda handler
    
    This function is used when deploying to AWS Lambda with API Gateway
    """
    from mangum import Mangum
    handler = Mangum(app)
    return handler(event, context)

# Run application (development only)
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting development server")
    uvicorn.run(app, host="0.0.0.0", port=8000)