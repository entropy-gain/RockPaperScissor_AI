"""SQL storage implementation for game data, user states, and LLM interactions."""

import aiosqlite
import sqlite3
import json
from typing import List, Dict, Any
import asyncio
from .storage import Storage, StorageError
from ..utils import setup_logging
from ..config.database import SQLITE_CONFIG

logger = setup_logging()

class SQLStorageError(StorageError):
    """Exception for SQL storage specific errors."""
    pass

class SQLStorage(Storage):
    """SQL storage management class."""
    
    def __init__(self):
        """Initialize SQLite storage."""
        self.db_path = SQLITE_CONFIG["db_path"]
        self.conn = None
        self.sync_conn = None  # Synchronous connection
        self.write_queue = asyncio.Queue()
        self._init_task = None
    
    async def initialize(self):
        """Initialize database connection and create tables if they don't exist."""
        if self._init_task is None:
            self._init_task = asyncio.create_task(self._init_db())
            await self._init_task
            # Start the write queue processor
            asyncio.create_task(self._process_write_queue())
    
    async def _init_db(self):
        """Initialize database tables."""
        try:
            # Initialize async connection
            self.conn = await aiosqlite.connect(
                self.db_path,
                timeout=SQLITE_CONFIG["timeout"]
            )
            
            # Initialize sync connection
            self.sync_conn = sqlite3.connect(
                self.db_path,
                timeout=SQLITE_CONFIG["timeout"],
                check_same_thread=False
            )
            self.sync_conn.row_factory = sqlite3.Row
            
            # Create tables if they don't exist
            async with self.conn:
                # Game rounds table - stores all game data except session_stats
                await self.conn.execute("""
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
                await self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_states (
                        user_id TEXT PRIMARY KEY,
                        model_name TEXT NOT NULL,
                        model_state TEXT NOT NULL,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # LLM interactions table - stores all LLMInteraction fields
                await self.conn.execute("""
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
                
            logger.info("Database tables created/verified successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    async def _process_write_queue(self):
        """Process write queue and batch write to database."""
        while True:
            batch = []
            try:
                # Collect up to 100 items from queue
                for _ in range(100):
                    try:
                        item = await asyncio.wait_for(self.write_queue.get(), timeout=1.0)
                        batch.append(item)
                    except asyncio.TimeoutError:
                        break
                
                if batch:
                    await self._save_batch(batch)
            except Exception as e:
                logger.error(f"Error processing write queue: {str(e)}")
                await asyncio.sleep(1)  # Wait before retrying
    
    async def _save_batch(self, batch: List[Dict[str, Any]]):
        """Save a batch of items to database."""
        try:
            async with self.conn:
                for item in batch:
                    if "user_move" in item:  # Game round
                        await self.conn.execute("""
                            INSERT INTO game_rounds 
                            (game_id, user_id, session_id, user_move, ai_move, 
                             result, model_name)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            item["game_id"],
                            item["user_id"],
                            item["session_id"],
                            item["user_move"],
                            item["ai_move"],
                            item["result"],
                            item["model_name"]
                        ))
                    elif "prompt" in item:  # LLM interaction
                        await self.conn.execute("""
                            INSERT INTO llm_interactions 
                            (prompt, response, llm_model_name, session_id, 
                             game_id, user_id, metadata)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            item["prompt"],
                            item["response"],
                            item["llm_model_name"],
                            item["session_id"],
                            item["game_id"],
                            item.get("user_id"),
                            json.dumps(item.get("metadata", {}))
                        ))
                    elif "model_state" in item:  # User state
                        await self.conn.execute("""
                            INSERT OR REPLACE INTO user_states 
                            (user_id, model_name, model_state)
                            VALUES (?, ?, ?)
                        """, (
                            item["user_id"],
                            item["model_name"],
                            json.dumps(item["model_state"])
                        ))
        except Exception as e:
            logger.error(f"Failed to save batch: {str(e)}")
    
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
    
    def get_user_state(self, user_id: str) -> Dict[str, Any]:
        """Get user state from database synchronously."""
        try:
            with self.sync_conn:
                cursor = self.sync_conn.execute("""
                    SELECT * FROM user_states 
                    WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    user_data = dict(row)
                    user_data["model_state"] = json.loads(user_data["model_state"])
                    return user_data
                return None
        except Exception as e:
            logger.error(f"Failed to get user state: {str(e)}")
            return None
    
    async def close(self) -> None:
        """Close the storage connection and ensure all queued data is processed."""
        try:
            # Wait for write queue to be empty
            if not self.write_queue.empty():
                logger.info("Waiting for write queue to be empty...")
                while not self.write_queue.empty():
                    await asyncio.sleep(0.1)
            
            # Process any remaining items in the queue
            if not self.write_queue.empty():
                logger.info("Processing remaining items in write queue...")
                batch = []
                while not self.write_queue.empty():
                    item = await self.write_queue.get()
                    batch.append(item)
                    if len(batch) >= self.batch_size:
                        await self._save_batch(batch)
                        batch = []
                if batch:
                    await self._save_batch(batch)
            
            # Close the database connection
            if self.conn:
                await self.conn.close()
            if self.sync_conn:
                self.sync_conn.close()
            
            logger.info("Storage connection closed successfully")
        except Exception as e:
            logger.error(f"Error during storage shutdown: {str(e)}")
            raise SQLStorageError(f"Failed to close storage: {str(e)}") 