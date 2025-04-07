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

logger = setup_logging()

class GameRepository:
    """Repository for game-related data operations."""
    
    def __init__(self):
        """Initialize the repository."""
        self.dynamodb = get_dynamodb_resource()
        self.games_table = self.dynamodb.Table('RockPaperScissor_Games')
    
    def create_new_round(self, session_id: Optional[str] = None, 
                         user_id: Optional[str] = None, 
                         ai_type: str = 'adaptive') -> Dict[str, Any]:
        """
        Create a new round in a session.
        
        Args:
            session_id: Existing session ID or None for new session
            user_id: User identifier (anonymous if None)
            ai_type: Type of AI to use
            
        Returns:
            Dictionary with game_id and session_id
        """
        game_id = str(uuid.uuid4())
        timestamp = int(time.time())
        
        # If no session_id provided, create a new one
        if not session_id:
            session_id = str(uuid.uuid4())
            
        # Get previous game in session for model state, if any
        previous_game = self._get_latest_game_in_session(session_id)
        
        # Initialize model state based on previous game or default
        if previous_game:
            # Use previous game's model state
            model_state = previous_game.get('model_state', {})
        else:
            # Initialize default model state
            model_state = {}
        
        # Create new game record
        game_item = {
            'game_id': game_id,
            'session_id': session_id,
            'user_id': user_id or 'anonymous',
            'created_at': timestamp,
            'updated_at': timestamp,
            'ai_type': ai_type,
            'player_move': None,  # Will be set when player makes a move
            'ai_move': None,      # Will be set when AI responds
            'game_result': None,       # Will be set when round is completed
            'model_state': self._convert_to_dynamodb_format(model_state),
            'round_complete': False
        }
        
        try:
            self.games_table.put_item(Item=game_item)
            logger.info(f"Created new round with game ID: {game_id} in session: {session_id}")
            return {
                'game_id': game_id,
                'session_id': session_id
            }
        except Exception as e:
            logger.error(f"Error creating new round: {str(e)}")
            raise
    
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
    
    def update_round_with_player_move(self, game_id: str, player_move: str) -> bool:
        """
        Update a round with the player's move.
        
        Args:
            game_id: The game ID
            player_move: Player's move (rock, paper, scissors)
            
        Returns:
            bool: Success or failure
        """
        try:
            response = self.games_table.update_item(
                Key={'game_id': game_id},
                UpdateExpression="SET player_move = :move, updated_at = :time",
                ExpressionAttributeValues={
                    ':move': player_move,
                    ':time': int(time.time())
                },
                ReturnValues="UPDATED_NEW"
            )
            
            logger.info(f"Updated game {game_id} with player move: {player_move}")
            return True
        except Exception as e:
            logger.error(f"Error updating player move: {str(e)}")
            return False
    
    def complete_round(self, game_id: str, ai_move: str, result: str, model_state: Dict[str, Any]) -> bool:
        """
        Complete a round with AI move, result and updated model state.
        
        Args:
            game_id: The game ID
            ai_move: AI's move (rock, paper, scissors)
            result: Result of the round (player_win, ai_win, draw)
            model_state: Updated AI model state
            
        Returns:
            bool: Success or failure
        """
        try:
            response = self.games_table.update_item(
                Key={'game_id': game_id},
                UpdateExpression="SET ai_move = :ai_move, game_result = :game_result, model_state = :model_state, round_complete = :complete, updated_at = :time",
                ExpressionAttributeValues={
                    ':ai_move': ai_move,
                    ':game_result': result,
                    ':model_state': self._convert_to_dynamodb_format(model_state),
                    ':complete': True,
                    ':time': int(time.time())
                },
                ReturnValues="UPDATED_NEW"
            )
            
            logger.info(f"Completed round {game_id} with AI move: {ai_move}, result: {result}")
            return True
        except Exception as e:
            logger.error(f"Error completing round: {str(e)}")
            return False
    
    def _get_latest_game_in_session(self, session_id: str) -> Optional[Dict[str, Any]]:
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
    
    def get_session_games(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
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