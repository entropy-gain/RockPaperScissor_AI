"""SQL storage implementation for game data, user states, and LLM interactions."""

import aiosqlite
import json
from typing import List, Dict, Any
import asyncio
from .storage import Storage, StorageError
from ..utils import setup_logging
from ..config.database import SQLITE_CONFIG

logger = setup_logging()

# Constants
BATCH_SIZE = 100  # Maximum number of items to process in a single batch
QUEUE_MAXSIZE = 10000  # Maximum number of items in write queue

class SQLStorageError(StorageError):
    """Exception for SQL storage specific errors."""
    pass

class SQLStorage(Storage):
    """SQL storage management class."""
    
    def __init__(self):
        """Initialize SQLite storage."""
        self.db_path = SQLITE_CONFIG["db_path"]
        self.pool = None  # Connection pool
        self.write_queue = asyncio.Queue(maxsize=QUEUE_MAXSIZE)
        self._init_task = None
        self._write_task = None
        self._write_queue_done = asyncio.Event()
    
    async def initialize(self):
        """Initialize database connection and create tables if they don't exist."""
        if self._init_task is None:
            self._init_task = asyncio.create_task(self._init_db())
            await self._init_task
            # Start the write queue processor
            if self._write_task is None:
                self._write_task = asyncio.create_task(self._process_write_queue())
        else:
            await self._init_task

    async def _init_db(self):
        """Initialize database tables."""
        try:
            # Initialize connection pool
            self.pool = await aiosqlite.connect(
                self.db_path,
                timeout=SQLITE_CONFIG["timeout"]
            )
            
            # Set row factory to return rows as dictionaries
            self.pool.row_factory = aiosqlite.Row
            
            # Create tables if they don't exist
            # Game rounds table - stores all game data except session_stats
            await self.pool.execute("""
                CREATE TABLE IF NOT EXISTS game_rounds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_move TEXT NOT NULL,
                    ai_move TEXT NOT NULL,
                    result TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    UNIQUE(game_id)
                )
            """)
            
            # User states table - stores model_state, session_stats and user_id
            await self.pool.execute("""
                CREATE TABLE IF NOT EXISTS user_states (
                    user_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    model_state TEXT NOT NULL,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # LLM interactions table - stores all LLMInteraction fields
            await self.pool.execute("""
                CREATE TABLE IF NOT EXISTS llm_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    llm_model_name TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    user_id TEXT,
                    metadata TEXT
                )
            """)
            
            await self.pool.commit()
            logger.info("Database tables created/verified successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise

    async def _process_write_queue(self):
        """Process write queue and batch write to database."""
        while not self._write_queue_done.is_set():
            batch = []
            try:
                # Collect up to BATCH_SIZE items from queue
                for _ in range(BATCH_SIZE):
                    try:
                        item = await asyncio.wait_for(self.write_queue.get(), timeout=1.0)
                        batch.append(item)
                    except asyncio.TimeoutError:
                        if self._write_queue_done.is_set():
                            return
                        pass
                
                if batch:
                    await self._save_batch(batch)
            except Exception as e:
                logger.error(f"Error processing write queue: {str(e)}")
                await asyncio.sleep(1)  # Wait before retrying

    async def _save_batch(self, batch: List[Dict[str, Any]]):
        """Save a batch of items to database using batch operations.
        
        Args:
            batch: List of items to save, each item is a dictionary containing the data
        """
        try:
            # Separate items by type
            game_rounds = []
            llm_interactions = []
            user_states = []
            
            for item in batch:
                if "user_move" in item:  # Game round
                    game_rounds.append((
                        item["game_id"],
                        item["user_id"],
                        item["session_id"],
                        item["user_move"],
                        item["ai_move"],
                        item["result"],
                        item["model_name"]
                    ))
                elif "prompt" in item:  # LLM interaction
                    llm_interactions.append((
                        item["prompt"],
                        item["response"],
                        item["llm_model_name"],
                        item["session_id"],
                        item["game_id"],
                        item.get("user_id"),
                        json.dumps(item.get("metadata", {}))
                    ))
                elif "model_state" in item:  # User state
                    user_states.append((
                        item["user_id"],
                        item["model_name"],
                        json.dumps(item["model_state"])
                    ))
            
            # Execute batch inserts for each type
            if game_rounds:
                await self.pool.executemany("""
                    INSERT INTO game_rounds 
                    (game_id, user_id, session_id, user_move, ai_move, 
                     result, model_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, game_rounds)
                logger.debug(f"Batch inserted {len(game_rounds)} game rounds")
            
            if llm_interactions:
                await self.pool.executemany("""
                    INSERT INTO llm_interactions 
                    (prompt, response, llm_model_name, session_id, 
                     game_id, user_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, llm_interactions)
                logger.debug(f"Batch inserted {len(llm_interactions)} LLM interactions")
            
            if user_states:
                # For user states, we need to handle each one individually due to INSERT OR REPLACE
                for user_state in user_states:
                    await self.pool.execute("""
                        INSERT OR REPLACE INTO user_states 
                        (user_id, model_name, model_state)
                        VALUES (?, ?, ?)
                    """, user_state)
                logger.debug(f"Updated {len(user_states)} user states")
            
            await self.pool.commit()
            logger.info(f"Successfully saved batch of {len(batch)} items")
            
        except Exception as e:
            logger.error(f"Failed to save batch: {str(e)}")
            raise  # Re-raise the exception to be handled by the caller

    async def save_game_round(self, data: Dict[str, Any]) -> bool:
        """Save a game round to SQLite asynchronously."""
        try:
            await self.write_queue.put(data)
            return True
        except Exception as e:
            logger.error(f"Failed to queue game round: {str(e)}")
            return False

    async def save_llm_interaction(self, data: Dict[str, Any]) -> bool:
        """Save a LLM interaction to SQLite asynchronously."""
        try:
            await self.write_queue.put(data)
            return True
        except Exception as e:
            logger.error(f"Failed to queue LLM interaction: {str(e)}")
            return False

    async def get_user_state(self, user_id: str) -> Dict[str, Any]:
        """Get user state from database asynchronously."""
        try:
            async with self.pool.execute("""
                SELECT * FROM user_states 
                WHERE user_id = ?
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    user_data = dict(row)
                    user_data["model_state"] = json.loads(user_data["model_state"])
                    return user_data
                return None
        except Exception as e:
            logger.error(f"Failed to get user state: {str(e)}")
            return None

    async def save_batch_game_rounds(self, game_data_list: List[Dict[str, Any]]) -> bool:
        """Save multiple game rounds to SQLite in a batch.
        
        Args:
            game_data_list: List of game data to save
            
        Returns:
            bool: True if all saves were successful, False otherwise
        """
        try:
            # Prepare all the data for batch insert
            values = []
            for data in game_data_list:
                values.append((
                    data["game_id"],
                    data["user_id"],
                    data["session_id"],
                    data["user_move"],
                    data["ai_move"],
                    data["result"],
                    data["model_name"]
                ))
            
            # Execute batch insert
            await self.pool.executemany("""
                INSERT INTO game_rounds 
                (game_id, user_id, session_id, user_move, ai_move, 
                 result, model_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, values)
            
            await self.pool.commit()
            logger.info(f"Successfully saved {len(game_data_list)} game rounds in batch")
            return True
        except Exception as e:
            logger.error(f"Failed to save batch game rounds: {str(e)}")
            return False

    async def save_batch_llm_interactions(self, interaction_data_list: List[Dict[str, Any]]) -> bool:
        """Save multiple LLM interactions to SQLite in a batch.
        
        Args:
            interaction_data_list: List of LLM interaction data to save
            
        Returns:
            bool: True if all saves were successful, False otherwise
        """
        try:
            # Prepare all the data for batch insert
            values = []
            for data in interaction_data_list:
                values.append((
                    data["prompt"],
                    data["response"],
                    data["llm_model_name"],
                    data["session_id"],
                    data["game_id"],
                    data.get("user_id"),
                    json.dumps(data.get("metadata", {}))
                ))
            
            # Execute batch insert
            await self.pool.executemany("""
                INSERT INTO llm_interactions 
                (prompt, response, llm_model_name, session_id, 
                 game_id, user_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, values)
            
            await self.pool.commit()
            logger.info(f"Successfully saved {len(interaction_data_list)} LLM interactions in batch")
            return True
        except Exception as e:
            logger.error(f"Failed to save batch LLM interactions: {str(e)}")
            return False

    async def close(self) -> None:
        """Close the storage connection and ensure all queued data is processed."""
        try:
            logger.info("Closing storage...")
            
            # Stop background writer
            self._write_queue_done.set()
            
            # Wait for background task to finish
            if self._write_task:
                await self._write_task
            
            # Flush remaining items in queue
            batch = []
            while not self.write_queue.empty():
                batch.append(await self.write_queue.get())
                if len(batch) >= BATCH_SIZE:
                    await self._save_batch(batch)
                    batch = []
            if batch:
                await self._save_batch(batch)
            
            # Close the database connection
            if self.pool:
                await self.pool.close()
            
            logger.info("Storage closed successfully")
        except Exception as e:
            logger.error(f"Error during storage shutdown: {str(e)}")
            raise SQLStorageError(f"Failed to close storage: {str(e)}")