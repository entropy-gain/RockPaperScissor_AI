import boto3
import json
import uuid
import time
from decimal import Decimal
from typing import Dict, Any, Optional, List
import numpy as np
from boto3.dynamodb.conditions import Key
from ..utils.logging import setup_logging
from .db import get_dynamodb_resource, create_tables_if_not_exist
from ..schemas.game import GameRequest, GameResponse, GameData


logger = setup_logging()

class GameRepository:
    """Repository for game-related data operations."""
    
    def __init__(self):
        """Initialize the repository."""
        self.dynamodb = get_dynamodb_resource()
        self.games_table = self.dynamodb.Table('RockPaperScissor_Games')
    
    
    
    def save_game(self, game_data: GameData) -> bool:
        """
        Save or update a game in DynamoDB.
        
        Args:
            game_id: Unique identifier for the game
            session_id: Session identifier
            ai_type: Type of AI opponent
            user_move: Player's choice (rock, paper, scissors)
            ai_move: AI's choice (rock, paper, scissors)
            result: Game result (player_win, ai_win, draw)
            model_state: AI model state for learning
            session_stats: Current session statistics
            user_id: User identifier
            
        Returns:
            bool: Success or failure
        """
        try:
            current_time = int(time.time())
            
            # Convert model state and session stats to DynamoDB format
            dynamodb_model_state = self._convert_to_dynamodb_format(game_data.model_state)
            dynamodb_session_stats = self._convert_to_dynamodb_format(game_data.session_stats)
            
            # Check if the game already exists
            response = self.games_table.get_item(
                Key={'game_id': game_data.game_id},
                ProjectionExpression="game_id"
            )

            if 'Item' not in response:
                # Game doesn't exist, create a new one
                item = {
                    'game_id': game_data.game_id,
                    'user_id': game_data.user_id,
                    'session_id': game_data.session_id,
                    'ai_type': game_data.ai_type,
                    'user_move': game_data.user_move,
                    'ai_move': game_data.ai_move,
                    'game_result': game_data.result,
                    'model_state': dynamodb_model_state,
                    'session_stats': dynamodb_session_stats,
                    'created_at': current_time,
                }
                self.games_table.put_item(Item=item)
                logger.info(f"Created new game {game_data.game_id} for user {game_data.user_id} in session {game_data.session_id}")
            else:
                # Game exists, update it
                self.games_table.update_item(
                    Key={'game_id': game_data.game_id},
                    UpdateExpression="SET ai_move = :ai_move, user_move = :user_move, " 
                                    "game_result = :result, model_state = :model_state, "
                                    "session_stats = :session_stats, session_id = :session_id, "
                                    "user_id = :user_id, ai_type = :ai_type, created_at = :time",
                    ExpressionAttributeValues={
                        ':ai_move': game_data.ai_move,
                        ':user_move': game_data.user_move,
                        ':result': game_data.result,
                        ':model_state': dynamodb_model_state,
                        ':session_stats': dynamodb_session_stats,
                        ':session_id': game_data.session_id,
                        ':user_id': game_data.user_id,
                        ':ai_type': game_data.ai_type,
                        ':time': current_time
                    },
                    ReturnValues="UPDATED_NEW"
                )
                logger.info(f"Updated game {game_data.game_id} for user {game_data.user_id}")
            
            # No need to update session records separately as we use composite indexes
            # (user_id, session_id, game_id) to query session-related data
            
            return True
        except Exception as e:
            logger.error(f"Error saving game: {str(e)}")
            return False
    
    def get_latest_game_in_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent game in a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            Latest game record or None
        """
        try:
            response = self.games_table.query(
                IndexName='SessionIndex',
                KeyConditionExpression=Key('session_id').eq(session_id),
                ScanIndexForward=False,  # Descending order by sort key
                Limit=1
            )
            
            items = response.get('Items', [])
            if items:
                game = items[0]
                if 'model_state' in game:
                    game['model_state'] = self._convert_from_dynamodb_format(game['model_state'])
                return game
            return None
        except Exception as e:
            logger.error(f"Error getting latest game in session {session_id}: {str(e)}")
            return None
    
    def get_game(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get game details by ID."""
        try:
            response = self.games_table.get_item(Key={'game_id': game_id})
            item = response.get('Item')
            
            if item:
                # Convert DynamoDB format back to Python types
                if 'model_state' in item:
                    item['model_state'] = self._convert_from_dynamodb_format(item['model_state'])
                
                return item
            return None
        except Exception as e:
            logger.error(f"Error retrieving game {game_id}: {str(e)}")
            return None
    
    def get_session_games(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent games for a session.
        
        Args:
            session_id: The session ID
            limit: Maximum number of games to return
            
        Returns:
            List of game records sorted by created_at (most recent first)
        """
        try:
            response = self.games_table.query(
                IndexName='SessionIndex',
                KeyConditionExpression=Key('session_id').eq(session_id),
                ScanIndexForward=False,  # Descending order by sort key
                Limit=limit
            )
            
            games = response.get('Items', [])
            for game in games:
                if 'model_state' in game:
                    game['model_state'] = self._convert_from_dynamodb_format(game['model_state'])
            
            return games
        except Exception as e:
            logger.error(f"Error retrieving games for session {session_id}: {str(e)}")
            return []
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get aggregated statistics for a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            Dictionary with session statistics
        """
        try:
            games = self.get_session_games(session_id, limit=1000)  # Get all games in session
            completed_games = [g for g in games if g.get('round_complete', False)]
            
            stats = {
                'total_rounds': len(completed_games),
                'player_wins': sum(1 for g in completed_games if g.get('game_result') == 'player_win'),
                'ai_wins': sum(1 for g in completed_games if g.get('game_result') == 'ai_win'),
                'draws': sum(1 for g in completed_games if g.get('game_result') == 'draw'),
                'ai_type': games[0].get('ai_type') if games else None,
                'session_id': session_id,
                'user_id': games[0].get('user_id') if games else None
            }
            
            # Calculate win rate
            if stats['total_rounds'] > 0:
                stats['player_win_rate'] = (stats['player_wins'] / stats['total_rounds']) * 100
                stats['ai_win_rate'] = (stats['ai_wins'] / stats['total_rounds']) * 100
            else:
                stats['player_win_rate'] = 0
                stats['ai_win_rate'] = 0
                
            return stats
        except Exception as e:
            logger.error(f"Error getting session stats for {session_id}: {str(e)}")
            return {
                'total_rounds': 0,
                'player_wins': 0,
                'ai_wins': 0,
                'draws': 0,
                'session_id': session_id
            }
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate statistics for a specific user across all sessions
        
        Args:
            user_id (str): The user ID to query
            
        Returns:
            dict: User statistics
        """
        try:
            response = self.games_table.query(
                IndexName='UserIndex',  # Secondary index on user_id
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            
            games = response.get('Items', [])
            completed_games = [g for g in games if g.get('round_complete', False)]
            
            # Calculate statistics
            stats = {
                'total_rounds': len(completed_games),
                'player_wins': sum(1 for g in completed_games if g.get('game_result') == 'player_win'),
                'ai_wins': sum(1 for g in completed_games if g.get('game_result') == 'ai_win'),
                'draws': sum(1 for g in completed_games if g.get('game_result') == 'draw'),
                'by_ai': {},
                'sessions': len(set(g.get('session_id') for g in games))
            }
            
            # Calculate statistics per AI type
            ai_types = set(game.get('ai_type') for game in games if game.get('ai_type'))
            for ai_type in ai_types:
                ai_games = [g for g in completed_games if g.get('ai_type') == ai_type]
                stats['by_ai'][ai_type] = {
                    'total': len(ai_games),
                    'player_wins': sum(1 for g in ai_games if g.get('game_result') == 'player_win'),
                    'ai_wins': sum(1 for g in ai_games if g.get('game_result') == 'ai_win'),
                    'draws': sum(1 for g in ai_games if g.get('game_result') == 'draw')
                }
                
                # Calculate win rate per AI type
                if stats['by_ai'][ai_type]['total'] > 0:
                    stats['by_ai'][ai_type]['player_win_rate'] = (
                        stats['by_ai'][ai_type]['player_wins'] / stats['by_ai'][ai_type]['total']
                    ) * 100
                else:
                    stats['by_ai'][ai_type]['player_win_rate'] = 0
            
            # Calculate overall win rate
            if stats['total_rounds'] > 0:
                stats['player_win_rate'] = (stats['player_wins'] / stats['total_rounds']) * 100
            else:
                stats['player_win_rate'] = 0
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {
                'total_rounds': 0, 
                'player_wins': 0, 
                'ai_wins': 0, 
                'draws': 0, 
                'by_ai': {}, 
                'sessions': 0,
                'player_win_rate': 0
            }
    
    def get_ai_performance(self) -> List[Dict[str, Any]]:
        """
        Calculate performance metrics for all AI types
        
        Returns:
            list: AI performance data sorted by win rate
        """
        try:
            # Scan all completed game records
            response = self.games_table.scan(
                FilterExpression='round_complete = :complete',
                ExpressionAttributeValues={':complete': True}
            )
            games = response.get('Items', [])
            
            # Get all items if there's pagination
            while 'LastEvaluatedKey' in response:
                response = self.games_table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey'],
                    FilterExpression='round_complete = :complete',
                    ExpressionAttributeValues={':complete': True}
                )
                games.extend(response.get('Items', []))
            
            # Group by AI type
            ai_stats = {}
            
            for game in games:
                ai_type = game.get('ai_type')
                result = game.get('game_result')
                
                if not ai_type or not result:
                    continue
                
                if ai_type not in ai_stats:
                    ai_stats[ai_type] = {'ai_wins': 0, 'player_wins': 0, 'draws': 0, 'total': 0}
                
                ai_stats[ai_type]['total'] += 1
                
                if result == 'player_win':
                    ai_stats[ai_type]['player_wins'] += 1
                elif result == 'ai_win':
                    ai_stats[ai_type]['ai_wins'] += 1
                else:  # draw
                    ai_stats[ai_type]['draws'] += 1
            
            # Calculate win rates and format for response
            result_list = []
            
            for ai_type, stats in ai_stats.items():
                total = stats['total']
                if total > 0:
                    ai_win_rate = (stats['ai_wins'] / total) * 100
                    player_win_rate = (stats['player_wins'] / total) * 100
                else:
                    ai_win_rate = 0
                    player_win_rate = 0
                
                result_list.append({
                    'name': ai_type,
                    'ai_win_rate': round(ai_win_rate, 1),
                    'player_win_rate': round(player_win_rate, 1),
                    'ai_wins': stats['ai_wins'],
                    'player_wins': stats['player_wins'],
                    'draws': stats['draws'],
                    'total_rounds': stats['total']
                })
            
            # Sort by AI win rate (descending)
            result_list.sort(key=lambda x: x['ai_win_rate'], reverse=True)
            return result_list
        
        except Exception as e:
            logger.error(f"Error getting AI performance: {str(e)}")
            return []
    
    def _convert_to_dynamodb_format(self, data: Any) -> Any:
        """Convert Python data types to DynamoDB compatible format."""
        if isinstance(data, dict):
            return {k: self._convert_to_dynamodb_format(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_to_dynamodb_format(i) for i in data]
        elif isinstance(data, (int, float)):
            return Decimal(str(data))
        elif isinstance(data, np.ndarray):
            return [self._convert_to_dynamodb_format(i) for i in data.tolist()]
        else:
            return data
    
    def _convert_from_dynamodb_format(self, data: Any) -> Any:
        """Convert DynamoDB data types back to Python types."""
        if isinstance(data, dict):
            return {k: self._convert_from_dynamodb_format(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_from_dynamodb_format(i) for i in data]
        elif isinstance(data, Decimal):
            return float(data)
        else:
            return data