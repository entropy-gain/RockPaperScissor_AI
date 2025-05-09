"""
LLM Cache module for storing LLM prompts and responses.
"""
from typing import List
import time
import asyncio
import signal
from ..utils.logging import setup_logging
from ..schemas.game import LLMInteraction
from ..repositories import Storage

logger = setup_logging()

class LLMCache:
    def __init__(
        self,
        storage: Storage,
        batch_size: int = 100,            # Flush buffer after 100 records
        batch_timeout_sec: int = 300      # Flush buffer after 5 minutes max
    ):
        # Storage instance
        self.storage = storage
        
        # Buffer for storing LLM interactions
        self.buffer: List[LLMInteraction] = []
        self.buffer_size = 0
        self.batch_size = batch_size
        self.batch_timeout_sec = batch_timeout_sec
        self.last_flush_time = time.time()
        
        # Async safety
        self.lock = asyncio.Lock()
        self._flush_lock = asyncio.Lock()  # Lock for flush operations
        self._is_flushing = False  # Flag to track if a flush is in progress
        self._flush_event = asyncio.Event()  # Event to signal flush completion
        self._shutdown_event = asyncio.Event()  # Event to signal shutdown
        
        # Start background flush task
        self._start_background_flush()
        
        # Register shutdown handler
        self._register_shutdown_handler()
    
    def _register_shutdown_handler(self):
        """Register signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self._shutdown_event.set()
            logger.info("Shutdown signal sent")
        
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
            if self.buffer:
                logger.info("Performing final flush before shutdown...")
                try:
                    await self.execute_batch_flush()
                except Exception as e:
                    logger.error(f"Error during final flush: {str(e)}")
        
        # Create and start the background task
        loop = asyncio.get_event_loop()
        self._flush_task = loop.create_task(periodic_flush())
    
    async def add_interaction(
        self, 
        prompt: str, 
        response: str,
        model_name: str,
        session_id: str,
        game_id: str,
        user_id: str = None,
        metadata: dict = None
    ) -> None:
        """
        Add a LLM interaction to the buffer
        
        Args:
            prompt: The prompt sent to LLM
            response: The response received from LLM
            model_name: Name of the LLM model used
            session_id: Associated game session ID
            game_id: Associated game ID
            user_id: Associated user ID
            metadata: Additional metadata about the interaction
        """
        async with self.lock:
            # Create interaction record
            interaction = LLMInteraction(
                prompt=prompt,
                response=response,
                model_name=model_name,
                session_id=session_id,
                game_id=game_id,
                user_id=user_id,
                metadata=metadata or {}
            )
            
            # Add to buffer
            self.buffer.append(interaction)
            self.buffer_size += 1
            logger.debug(f"Added LLM interaction to buffer, current size: {self.buffer_size}")
    
    def _check_batch_flush(self) -> bool:
        """Check if buffer should be flushed"""
        time_passed = time.time() - self.last_flush_time
        return (self.buffer_size >= self.batch_size or 
               (self.buffer and time_passed >= self.batch_timeout_sec))
    
    async def execute_batch_flush(self) -> bool:
        """
        Execute batch flush operation asynchronously
        
        Returns:
            bool: Whether the flush was successful
        """
        # First check if a flush is already in progress
        if self._flush_lock.locked():
            logger.debug("Another flush operation is in progress, skipping")
            return False

        await self._flush_lock.acquire()
        try:
            async with self.lock:
                if not self.buffer:
                    return False
                
                # Create a copy of the buffer to flush
                buffer_copy = self.buffer.copy()
                buffer_size = self.buffer_size
                
                # Clear the original buffer immediately
                self.buffer.clear()
                self.buffer_size = 0
                self.last_flush_time = time.time()
            
            # Convert LLMInteraction objects to dictionaries
            batch_data = [record.model_dump() for record in buffer_copy]
            logger.info(f"Executing LLM batch flush with {len(batch_data)} records")
            
            try:
                # Execute batch write using storage instance
                tasks = []
                for data in batch_data:
                    tasks.append(self.storage.save_llm_interaction(data))
                
                # Run all save operations concurrently
                results = await asyncio.gather(*tasks)
                
                # Check if all saves were successful
                success = all(results)
                if success:
                    logger.info("LLM batch flush completed successfully")
                else:
                    logger.error("Some LLM saves failed during batch flush")
                    # If any save failed, restore the data to buffer
                    async with self.lock:
                        self.buffer.extend(buffer_copy)
                        self.buffer_size = buffer_size
            except Exception as e:
                success = False
                logger.error(f"LLM storage flush failed: {str(e)}")
                # If failed, restore the data to buffer
                async with self.lock:
                    self.buffer.extend(buffer_copy)
                    self.buffer_size = buffer_size
            
            return success
        finally:
            self._flush_lock.release()
            self._flush_event.set()  # Signal that flush is complete

    async def shutdown(self):
        """Gracefully shutdown the cache, ensuring all data is saved"""
        logger.info("Initiating LLM cache shutdown...")
        self._shutdown_event.set()
        
        # Cancel the background flush task
        if hasattr(self, '_flush_task'):
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Wait for any ongoing flush to complete
        await self._flush_event.wait()
        
        # Final flush of any remaining data
        if self.buffer:
            logger.info("Performing final flush before shutdown...")
            try:
                await self.execute_batch_flush()
            except Exception as e:
                logger.error(f"Error during final flush: {str(e)}")
        
        logger.info("LLM cache shutdown complete")
    
    async def reset(self):
        """Reset all cache data asynchronously"""
        async with self.lock:
            self.buffer.clear()
            self.buffer_size = 0
            self.last_flush_time = time.time() 
            
    # async def force_flush(self) -> bool:
    #     """Force flush all data in buffer asynchronously"""
    #     async with self.lock:
    #         if not self.buffer:
    #             logger.debug("No LLM records to flush")
    #             return False
            
    #         logger.info("Force flushing all LLM records")
    #         return await self.execute_batch_flush()
    
    # async def get_buffer_size(self) -> int:
    #     """Get the number of records in the buffer"""
    #     async with self.lock:
    #         return self.buffer_size
    
    