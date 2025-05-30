# RockPaperScissor/repositories/sql_storage.py
from .storage import Storage
from typing import Dict, Any, Optional
import sqlite3
import json
import asyncio
from pathlib import Path
from datetime import datetime
import numpy as np

class SQLStorage(Storage):
    def __init__(self, db_path: str = "data/game_history.db"):
        self.db_path = db_path
        self.conn = None
        self._ensure_db_directory()
        
    def _ensure_db_directory(self):
        """Ensure the database directory exists"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self):
        """Initialize the database connection and create tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Create game_sessions table with completion status
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_sessions (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                total_rounds INTEGER DEFAULT 0,
                player_wins INTEGER DEFAULT 0,
                ai_wins INTEGER DEFAULT 0,
                draws INTEGER DEFAULT 0,
                is_completed BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Create game_rounds table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_rounds (
                round_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                round_number INTEGER,
                player_move TEXT,
                ai_move TEXT,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES game_sessions(session_id)
            )
        ''')
        
        # Create ai_states table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_states (
                session_id TEXT,
                ai_type TEXT,
                state_data TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (session_id, ai_type),
                FOREIGN KEY (session_id) REFERENCES game_sessions(session_id)
            )
        ''')
        
        self.conn.commit()

    async def save_game_round(self, game_data: Dict[str, Any]) -> bool:
        """Save a game round to the database"""
        try:
            cursor = self.conn.cursor()
            session_id = game_data.get('game_id')
            
            # Update or insert game session
            cursor.execute('''
                INSERT INTO game_sessions (session_id, total_rounds, player_wins, ai_wins, draws)
                VALUES (?, 1, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    total_rounds = total_rounds + 1,
                    player_wins = player_wins + ?,
                    ai_wins = ai_wins + ?,
                    draws = draws + ?
            ''', (
                session_id,
                1 if game_data['result'] == 'player_win' else 0,
                1 if game_data['result'] == 'ai_win' else 0,
                1 if game_data['result'] == 'draw' else 0,
                1 if game_data['result'] == 'player_win' else 0,
                1 if game_data['result'] == 'ai_win' else 0,
                1 if game_data['result'] == 'draw' else 0
            ))
            
            # Get current round number
            cursor.execute('''
                SELECT COUNT(*) FROM game_rounds WHERE session_id = ?
            ''', (session_id,))
            round_number = cursor.fetchone()[0] + 1
            
            # Insert game round
            cursor.execute('''
                INSERT INTO game_rounds (session_id, round_number, player_move, ai_move, result)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                session_id,
                round_number,
                game_data['player_move'],
                game_data['ai_move'],
                game_data['result']
            ))
            
            # Save AI state if provided
            if 'ai_state' in game_data:
                def convert_ndarray(obj):
                    if isinstance(obj, np.ndarray):
                        return obj.tolist()
                    if isinstance(obj, dict):
                        return {k: convert_ndarray(v) for k, v in obj.items()}
                    if isinstance(obj, list):
                        return [convert_ndarray(x) for x in obj]
                    return obj
                ai_state_serializable = convert_ndarray(game_data['ai_state'])
                cursor.execute('''
                    INSERT INTO ai_states (session_id, ai_type, state_data)
                    VALUES (?, ?, ?)
                    ON CONFLICT(session_id, ai_type) DO UPDATE SET
                        state_data = ?,
                        last_updated = CURRENT_TIMESTAMP
                ''', (
                    session_id,
                    game_data.get('ai_type', 'adaptive_markov'),
                    json.dumps(ai_state_serializable),
                    json.dumps(ai_state_serializable)
                ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error saving game round: {e}")
            self.conn.rollback()
            return False

    async def complete_session(self, session_id: str) -> bool:
        """Mark a game session as completed"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE game_sessions
                SET is_completed = TRUE,
                    completed_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (session_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error completing session: {e}")
            self.conn.rollback()
            return False

    async def get_game_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve game history for a session"""
        try:
            cursor = self.conn.cursor()
            
            # Get session stats
            cursor.execute('''
                SELECT total_rounds, player_wins, ai_wins, draws, is_completed, completed_at
                FROM game_sessions
                WHERE session_id = ?
            ''', (session_id,))
            session_data = cursor.fetchone()
            
            if not session_data:
                return None
                
            # Get all rounds
            cursor.execute('''
                SELECT round_number, player_move, ai_move, result, created_at
                FROM game_rounds
                WHERE session_id = ?
                ORDER BY round_number
            ''', (session_id,))
            rounds = cursor.fetchall()
            
            return {
                'session_id': session_id,
                'total_rounds': session_data[0],
                'player_wins': session_data[1],
                'ai_wins': session_data[2],
                'draws': session_data[3],
                'is_completed': session_data[4],
                'completed_at': session_data[5],
                'rounds': [
                    {
                        'round_number': r[0],
                        'player_move': r[1],
                        'ai_move': r[2],
                        'result': r[3],
                        'created_at': r[4]
                    }
                    for r in rounds
                ]
            }
            
        except Exception as e:
            print(f"Error retrieving game history: {e}")
            return None

    async def get_ai_state(self, session_id: str, ai_type: str) -> Optional[Dict[str, Any]]:
        """Retrieve AI state for a session"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT state_data
                FROM ai_states
                WHERE session_id = ? AND ai_type = ?
            ''', (session_id, ai_type))
            
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            return None
            
        except Exception as e:
            print(f"Error retrieving AI state: {e}")
            return None

    async def close(self) -> None:
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None