import asyncio
import os
from pathlib import Path
from RockPaperScissor.repositories.sql_storage import SQLStorage
from RockPaperScissor.config import database

async def main():
    # Set a temporary SQLite path for testing
    test_db_path = Path(__file__).parent / "test_manual_db.sqlite"
    database.SQLITE_CONFIG["db_path"] = str(test_db_path)

    # Create storage instance
    storage = SQLStorage()
    await storage.initialize()
    print("✅ Initialization complete")

    # Test writing a game_round record
    result = await storage.save_game_round({
        "game_id": "game_test_001",
        "user_id": "user_001",
        "session_id": "session_001",
        "user_move": "rock",
        "ai_move": "paper",
        "result": "ai_win",
        "model_name": "test_model_v1"
    })
    print(f"✅ Write game_round result: {result}")

    
    # Test writing user_state
    await storage.write_queue.put({
        "user_id": "user_901",
        "model_name": "test_model_v1",
        "model_state": {"round": 42}
    })
    print("✅ user_state has been put into write queue")

    # Wait for the background write task to process the queue
    await asyncio.sleep(1.0)

    # Test reading user_state
    user_state = await storage.get_user_state("user_004")
    print(f"✅ Queried user_state: {user_state}")

    # Test batch writing game_round records
    batch_data = [
        {
            "game_id": f"game_test_batch_{i:04}",
            "user_id": f"user_{i:04}",
            "session_id": f"session_{i:04}",
            "user_move": "rock",
            "ai_move": "scissors",
            "result": "user_win" if i % 2 == 0 else "ai_win",
            "model_name": "test_model_v1"
        }
        for i in range(50)
    ]
    batch_result = await storage.save_batch_game_rounds(batch_data)
    print(f"✅ Batch write game_rounds result: {batch_result}")


    # Close storage
    await storage.close()
    print("✅ Storage closed")

    # Check if the database file was created
    if test_db_path.exists():
        print(f"✅ Database file created successfully: {test_db_path}")
    else:
        print("❌ Database file was not created")

if __name__ == "__main__":
    asyncio.run(main())
