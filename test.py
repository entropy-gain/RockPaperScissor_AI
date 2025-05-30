import sqlite3
from datetime import datetime
from tabulate import tabulate
import os

def check_database():
    # Check if database exists
    db_path = "data/game_history.db"
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return

    print("✅ Database file found!")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\n📊 Database Tables:")
        for table in tables:
            print(f"  - {table[0]}")

        # Get game sessions
        print("\n🎮 Game Sessions:")
        cursor.execute("""
            SELECT 
                session_id,
                total_rounds,
                player_wins,
                ai_wins,
                draws,
                is_completed,
                datetime(created_at) as start_time,
                datetime(completed_at) as end_time
            FROM game_sessions
            ORDER BY created_at DESC
        """)
        sessions = cursor.fetchall()
        
        if not sessions:
            print("  No game sessions found!")
        else:
            headers = ["Session ID", "Rounds", "Player Wins", "AI Wins", "Draws", "Completed", "Start Time", "End Time"]
            print(tabulate(sessions, headers=headers, tablefmt="grid"))

        # Get detailed round history for the most recent session
        if sessions:
            latest_session = sessions[0][0]  # Get the session_id of the most recent session
            print(f"\n🎲 Round History for Session {latest_session}:")
            cursor.execute("""
                SELECT 
                    round_number,
                    player_move,
                    ai_move,
                    result,
                    datetime(created_at) as time
                FROM game_rounds
                WHERE session_id = ?
                ORDER BY round_number
            """, (latest_session,))
            rounds = cursor.fetchall()
            
            if not rounds:
                print("  No rounds found for this session!")
            else:
                headers = ["Round", "Player Move", "AI Move", "Result", "Time"]
                print(tabulate(rounds, headers=headers, tablefmt="grid"))

        # Get AI states
        print("\n🤖 AI States:")
        cursor.execute("""
            SELECT 
                session_id,
                ai_type,
                datetime(last_updated) as last_updated
            FROM ai_states
            ORDER BY last_updated DESC
        """)
        ai_states = cursor.fetchall()
        
        if not ai_states:
            print("  No AI states found!")
        else:
            headers = ["Session ID", "AI Type", "Last Updated"]
            print(tabulate(ai_states, headers=headers, tablefmt="grid"))

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔍 Checking Rock Paper Scissors Database...")
    check_database() 