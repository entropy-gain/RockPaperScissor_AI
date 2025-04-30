from collections import defaultdict, deque
import time
from typing import Any, Optional, Dict
from ..schemas.game import GameData, GameRecord
import threading
import asyncio
import signal
from ..utils import setup_logging
from ..repositories import Storage


logger = setup_logging()

class GameSessionCache:
    def __init__(
        self, 
        storage: Storage,
        max_age_sec: int = 300,           # Flush session records after 5 minutes max
        batch_size: int = 100,            # Flush buffer after 100 total records
        batch_timeout_sec: int = 300       # Flush buffer after 5 minute max
    ):
        # Storage instance
        self.storage = storage
        
        # Session-level storage - just keep the most recent records
        self.session_queues = defaultdict(deque)
        self.session_last_update = defaultdict(time.time)  # Track last update time for each session
        
        # Configuration parameters
        self.max_age_sec = max_age_sec
        
        # Buffer for storing game records
        self.buffer: Dict[str, GameRecord] = {}
        self.buffer_size = 0
        self.batch_size = batch_size
        self.batch_timeout_sec = batch_timeout_sec
        self.last_flush_time = time.time()
        
        # Thread safety
        self.lock = threading.RLock()
        self._flush_lock = threading.Lock()  # Lock for flush operations
        self._is_flushing = False  # Flag to track if a flush is in progress
        self._flush_event = threading.Event()  # Event to signal flush completion
        self._shutdown_event = threading.Event()  # Event to signal shutdown
        
        # Start background flush task
        self._start_background_flush()
        
        # Register shutdown handler
        self._register_shutdown_handler()
    
    def _register_shutdown_handler(self):
        """Register signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self._shutdown_event.set()
            # Wait for flush to complete
            self._flush_event.wait(timeout=10)  # Wait up to 10 seconds
            logger.info("Shutdown complete")
        
        # Register handlers for common termination signals
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    def _start_background_flush(self):
        """Start background task for periodic buffer flushing"""
        async def periodic_flush():
            while not self._shutdown_event.is_set():
                try:
                    await asyncio.sleep(60)  # Check every minute
                    if self._check_batch_flush():
                        await self.execute_batch_flush()
                except asyncio.CancelledError:
                    logger.info("Background flush task cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in background flush task: {str(e)}")
            
            # Final flush before shutdown
            if self.buffer or any(self.session_queues.values()):
                logger.info("Performing final flush before shutdown...")
                try:
                    # Move all session records to buffer
                    with self.lock:
                        for session_id, queue in list(self.session_queues.items()):
                            if queue:
                                for record in list(queue):
                                    self.buffer[record.game_id] = record
                                    self.buffer_size += 1
                                queue.clear()
                    
                    # Execute final flush
                    if self.buffer:
                        await self.execute_batch_flush()
                except Exception as e:
                    logger.error(f"Error during final flush: {str(e)}")
        
        # Create and start the background task
        loop = asyncio.get_event_loop()
        self._flush_task = loop.create_task(periodic_flush())
    
    def add_record(self, session_id: Any, record: GameData) -> None:
        """
        Add a game record to the specified session's cache
        """
        with self.lock:
            # Update session's last update time
            self.session_last_update[session_id] = time.time()
            
            # If there's already a record for this session, move it to flush buffer
            if session_id in self.session_queues and self.session_queues[session_id]:
                old_record = self.session_queues[session_id][0]
                self.buffer[old_record.game_id] = old_record  # Only store GameData
                self.buffer_size += 1
                logger.debug(f"Moving old record to flush buffer for session {session_id}")
                self.session_queues[session_id].clear()  # Clear existing record
            
            # Add new record to session queue
            self.session_queues[session_id].append(record)
            logger.debug(f"Added new record to session {session_id}")
    
    def _check_batch_flush(self) -> bool:
        """Check if batch buffer should be flushed"""
        time_passed = time.time() - self.last_flush_time
        return (self.buffer_size >= self.batch_size or 
               (self.buffer and time_passed >= self.batch_timeout_sec))
    
    def get_latest_record(self, session_id: Any) -> Optional[GameData]:
        """Get the most recent record for a session"""
        with self.lock:
            if session_id in self.session_queues and self.session_queues[session_id]:
                return self.session_queues[session_id][-1]
            return None
    
    
    async def execute_batch_flush(self) -> bool:
        """
        Execute batch flush operation using the storage instance.
        This method is synchronous but internally uses async storage operations.
        """
        # First check if a flush is already in progress
        if not self._flush_lock.acquire(blocking=False):
            logger.debug("Another flush operation is in progress, skipping")
            return False

        try:
            with self.lock:
                if not self.buffer:
                    return False
                
                # Create a copy of the buffer to flush
                buffer_copy = self.buffer.copy()
                buffer_size = self.buffer_size
                
                # Clear the original buffer immediately
                self.buffer.clear()
                self.buffer_size = 0
                self.last_flush_time = time.time()
            
            # Convert GameData objects to dictionaries
            batch_data = [record.model_dump() for record in buffer_copy.values()]
            logger.info(f"Executing batch flush with {len(batch_data)} records")
            
            try:
                # Create a new event loop for async operations
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Execute batch write using storage instance
                async def save_all():
                    tasks = []
                    for data in batch_data:
                        tasks.append(self.storage.save_game_record(data))
                    return await asyncio.gather(*tasks)
                
                # Run all save operations concurrently
                results = loop.run_until_complete(save_all())
                loop.close()
                
                # Check if all saves were successful
                success = all(results)
                if success:
                    logger.info("Batch flush completed successfully")
                else:
                    logger.error("Some saves failed during batch flush")
                    # If any save failed, restore the data to buffer
                    with self.lock:
                        self.buffer.update(buffer_copy)
                        self.buffer_size = buffer_size
            except Exception as e:
                success = False
                logger.error(f"Storage flush failed: {str(e)}")
                # If failed, restore the data to buffer
                with self.lock:
                    self.buffer.update(buffer_copy)
                    self.buffer_size = buffer_size
            
            # Clean up inactive sessions after successful flush
            if success:
                self.clean_inactive_sessions()
            
            return success
        finally:
            self._flush_lock.release()
            self._flush_event.set()  # Signal that flush is complete
    
    def move_session_to_buffer(self, session_id: Any) -> bool:
        """
        Move session data to flush buffer without forcing a flush.
        This is used when ending a game session.
        
        Args:
            session_id: The session ID to move to buffer
            
        Returns:
            bool: True if session data was moved, False if no data to move
        """
        with self.lock:
            if session_id not in self.session_queues or not self.session_queues[session_id]:
                logger.debug(f"No records to move to buffer for session {session_id}")
                return False
            
            # Get the record for this session
            record = self.session_queues[session_id][0]
            logger.info(f"Moving session {session_id} data to flush buffer")
            
            # Move it to flush buffer
            self.buffer[record.game_id] = record  # Only store GameData
            self.buffer_size += 1
            
            # Clear the session queue
            self.session_queues[session_id].clear()
            
            return True
    
    def clean_inactive_sessions(self):
        """Remove session data for inactive sessions based on last update time"""
        with self.lock:
            current_time = time.time()
            inactive_sessions = []
            
            # First collect all inactive sessions
            for session_id, last_update in list(self.session_last_update.items()):
                if current_time - last_update > self.max_age_sec:
                    inactive_sessions.append(session_id)
            
            if inactive_sessions:
                logger.info(f"Cleaning {len(inactive_sessions)} inactive sessions")
                # Then remove them in a single operation
                for session_id in inactive_sessions:
                    self.session_queues.pop(session_id, None)
                    self.session_last_update.pop(session_id, None)
                logger.debug(f"Cleaned sessions: {inactive_sessions}")

#--------------------------------temporary functions--------------------------------

    def check_and_flush(self) -> bool:
        """
        Check if batch flush is needed and execute if necessary
        Suitable for calling from a scheduled task
        """
        with self.lock:
            if self._check_batch_flush():
                return self.execute_batch_flush()
            return False
    
    def force_flush_all(self) -> bool:
        """Force flush all data (all sessions and buffer)"""
        with self.lock:
            logger.info("Force flushing all sessions")
            # Move all session records to flush buffer
            for session_id, queue in list(self.session_queues.items()):
                if queue:
                    for record in list(queue):
                        self.buffer[record.game_id] = record
                        self.buffer_size += 1
                    
                    queue.clear()
            
            # Execute batch flush if buffer has data
            if self.buffer:
                return self.execute_batch_flush()
            logger.debug("No records to flush")
        return False
    
    def get_session_count(self) -> int:
        """Get the number of active sessions in cache"""
        with self.lock:
            return len(self.session_queues)
    
    def get_buffer_size(self) -> int:
        """Get the number of records in the flush buffer"""
        with self.lock:
            return self.buffer_size
    
    async def reset(self):
        """Reset all cache data"""
        with self.lock:
            self.session_queues.clear()
            self.session_last_update.clear()
            self.buffer.clear()
            self.buffer_size = 0
            self.last_flush_time = time.time()

    async def shutdown(self):
        """Gracefully shutdown the cache, ensuring all data is saved"""
        logger.info("Initiating cache shutdown...")
        self._shutdown_event.set()
        
        # Cancel the background flush task
        if hasattr(self, '_flush_task'):
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Wait for any ongoing flush to complete
        self._flush_event.wait(timeout=10)  # Wait up to 10 seconds
        
        # Final flush of all data
        logger.info("Performing final flush before shutdown...")
        try:
            with self.lock:
                # First, move all session records to buffer
                for session_id, queue in list(self.session_queues.items()):
                    if queue:
                        for record in list(queue):
                            self.buffer[record.game_id] = record
                            self.buffer_size += 1
                        queue.clear()
                
                # Also clean up any inactive sessions
                self.clean_inactive_sessions()
            
            # Execute final flush if buffer has data
            if self.buffer:
                await self.execute_batch_flush()
            
            logger.info("Final flush completed successfully")
        except Exception as e:
            logger.error(f"Error during final flush: {str(e)}")
        
        logger.info("Cache shutdown complete")

    