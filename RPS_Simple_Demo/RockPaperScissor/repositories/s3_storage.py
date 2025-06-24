import boto3
import json
import sqlite3
import io
from datetime import datetime
from typing import Dict, Any, Optional
from .storage import Storage
import os
import numpy as np

class S3Storage(Storage):
    def __init__(self, bucket_name: str = None):
        self.bucket_name = bucket_name or os.getenv('AWS_S3_BUCKET_NAME')
        if not self.bucket_name:
            raise ValueError("S3 bucket name must be provided either through constructor or AWS_S3_BUCKET_NAME environment variable")
        
        # Configure S3 client with LocalStack endpoint if available
        endpoint_url = os.getenv('AWS_ENDPOINT_URL')
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
    def convert_ndarray(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, dict):
            return {k: self.convert_ndarray(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.convert_ndarray(x) for x in obj]
        return obj
        
    async def initialize(self):
        """Initialize S3 storage - verify bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except Exception as e:
            # If using LocalStack, create the bucket if it doesn't exist
            if os.getenv('AWS_ENDPOINT_URL'):
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                except Exception as create_error:
                    raise Exception(f"Failed to create S3 bucket {self.bucket_name}: {str(create_error)}")
            else:
                raise Exception(f"Failed to access S3 bucket {self.bucket_name}: {str(e)}")
            
    def _get_db_connection(self, session_id: str) -> sqlite3.Connection:
        """Get SQLite database connection for a session"""
        # Create in-memory database
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # Try to load existing data from S3
        try:
            s3_key = f"game_sessions/{session_id}/game.db"
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            db_data = response['Body'].read()
            conn.executescript(db_data.decode('utf-8'))
        except self.s3_client.exceptions.NoSuchKey:
            # No existing data, start with empty tables
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
        
        return conn

    def _save_db_to_s3(self, conn: sqlite3.Connection, session_id: str):
        """Save SQLite database to S3"""
        buffer = io.BytesIO()
        for line in conn.iterdump():
            buffer.write(f'{line}\n'.encode('utf-8'))
        buffer.seek(0)
        
        s3_key = f"game_sessions/{session_id}/game.db"
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=buffer.getvalue()
        )
            
    async def save_game_round(self, game_data: Dict[str, Any]) -> bool:
        """Save a game round to S3"""
        try:
            session_id = game_data.get('game_id')
            if not session_id:
                return False
                
            conn = self._get_db_connection(session_id)
            cursor = conn.cursor()
            
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
                ai_state_serializable = json.dumps(self.convert_ndarray(game_data['ai_state']))
                cursor.execute('''
                    INSERT INTO ai_states (session_id, ai_type, state_data)
                    VALUES (?, ?, ?)
                    ON CONFLICT(session_id, ai_type) DO UPDATE SET
                        state_data = ?,
                        last_updated = CURRENT_TIMESTAMP
                ''', (
                    session_id,
                    game_data.get('ai_type', 'adaptive_markov'),
                    ai_state_serializable,
                    ai_state_serializable
                ))
            
            # Save to S3
            self._save_db_to_s3(conn, session_id)
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error saving game round to S3: {e}")
            return False
            
    async def save_full_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Save the complete game session to S3"""
        try:
            conn = self._get_db_connection(session_id)
            cursor = conn.cursor()
            
            # Insert or update the session summary
            cursor.execute('''
                INSERT INTO game_sessions (session_id, total_rounds, player_wins, ai_wins, draws, is_completed, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(session_id) DO UPDATE SET
                    total_rounds = excluded.total_rounds,
                    player_wins = excluded.player_wins,
                    ai_wins = excluded.ai_wins,
                    draws = excluded.draws,
                    is_completed = excluded.is_completed,
                    completed_at = excluded.completed_at
            ''', (
                session_id,
                session_data['total_rounds'],
                session_data['player_wins'],
                session_data['ai_wins'],
                session_data['draws'],
                True
            ))
            
            # Delete existing rounds for this session
            cursor.execute('DELETE FROM game_rounds WHERE session_id = ?', (session_id,))
            
            print(f"[DEBUG] session_data['rounds']: {session_data['rounds']}")
            # Insert all rounds
            for round_data in session_data['rounds']:
                created_at = round_data.get('created_at', datetime.now().isoformat())
                cursor.execute('''
                    INSERT INTO game_rounds (session_id, round_number, player_move, ai_move, result, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    round_data['round_number'],
                    round_data['player_move'],
                    round_data['ai_move'],
                    round_data['result'],
                    created_at
                ))
            
            # Save AI state if available
            if session_data['rounds']:
                last_round = session_data['rounds'][-1]
                ai_type = last_round.get('ai_type', 'random')
                ai_state = last_round.get('ai_state', {})
                ai_state_serializable = json.dumps(self.convert_ndarray(ai_state))
                cursor.execute('''
                    INSERT INTO ai_states (session_id, ai_type, state_data)
                    VALUES (?, ?, ?)
                    ON CONFLICT(session_id, ai_type) DO UPDATE SET
                        state_data = ?,
                        last_updated = CURRENT_TIMESTAMP
                ''', (
                    session_id,
                    ai_type,
                    ai_state_serializable,
                    ai_state_serializable
                ))
            
            # Save to S3
            self._save_db_to_s3(conn, session_id)
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error saving full session to S3: {e}")
            return False
            
    async def get_game_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve game history for a session from S3"""
        try:
            conn = self._get_db_connection(session_id)
            cursor = conn.cursor()
            
            # Get session stats
            cursor.execute('''
                SELECT total_rounds, player_wins, ai_wins, draws, is_completed, completed_at
                FROM game_sessions
                WHERE session_id = ?
            ''', (session_id,))
            session_data = cursor.fetchone()
            
            if not session_data:
                conn.close()
                return None
                
            # Get all rounds
            cursor.execute('''
                SELECT round_number, player_move, ai_move, result, created_at
                FROM game_rounds
                WHERE session_id = ?
                ORDER BY round_number
            ''', (session_id,))
            rounds = cursor.fetchall()
            
            result = {
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
            
            conn.close()
            return result
            
        except Exception as e:
            print(f"Error retrieving game history from S3: {e}")
            return None
            
    async def close(self) -> None:
        """Close S3 client connection"""
        self.s3_client = None 