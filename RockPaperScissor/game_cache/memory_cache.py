# RockPaperScissor/game_cache/memory_cache.py
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class GameData:
    session_id: str
    player_move: str
    ai_move: str
    result: str
    ai_type: str
    ai_state: Dict[str, Any]
    created_at: datetime = datetime.now()

class GameSessionCache:
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._max_cache_size = 1000  # Maximum number of sessions to cache
        
    def update_session(self, session_id: str, game_data: Dict[str, Any]) -> None:
        """Update session data in cache"""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                'total_rounds': 0,
                'player_wins': 0,
                'ai_wins': 0,
                'draws': 0,
                'rounds': [],
                'last_updated': datetime.now()
            }
            
        session = self._sessions[session_id]
        
        # Update session stats
        session['total_rounds'] += 1
        if game_data['result'] == 'player_win':
            session['player_wins'] += 1
        elif game_data['result'] == 'ai_win':
            session['ai_wins'] += 1
        else:
            session['draws'] += 1
            
        # Add round data
        session['rounds'].append({
            'round_number': session['total_rounds'],
            'player_move': game_data['player_move'],
            'ai_move': game_data['ai_move'],
            'result': game_data['result'],
            'created_at': datetime.now()
        })
        
        # Update last updated timestamp
        session['last_updated'] = datetime.now()
        
        # Enforce cache size limit
        if len(self._sessions) > self._max_cache_size:
            self._remove_oldest_session()
            
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from cache"""
        return self._sessions.get(session_id)
        
    def _remove_oldest_session(self) -> None:
        """Remove the oldest session from cache"""
        if not self._sessions:
            return
            
        oldest_session = min(
            self._sessions.items(),
            key=lambda x: x[1]['last_updated']
        )
        del self._sessions[oldest_session[0]]
        
    def clear(self) -> None:
        """Clear all cached data"""
        self._sessions.clear()