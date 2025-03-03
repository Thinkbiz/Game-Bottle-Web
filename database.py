import sqlite3
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
import secrets
import hashlib
import json

from config import DB_PATH, DATA_DIR

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

@dataclass
class LeaderboardEntry:
    player_name: str
    score: int
    xp: int
    victory_type: str
    health: int
    date: datetime

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create players table (previous missing)
    c.execute('''
        CREATE TABLE IF NOT EXISTS players
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         name TEXT UNIQUE,
         last_played TIMESTAMP,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    
    # Create leaderboard table
    c.execute('''
        CREATE TABLE IF NOT EXISTS leaderboard
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         player_name TEXT,
         score INTEGER,
         xp INTEGER,
         victory_type TEXT,
         health INTEGER,
         date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    
    # Create users table with magic link authentication
    c.execute('''
        CREATE TABLE IF NOT EXISTS users
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         email TEXT UNIQUE,
         display_name TEXT,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         last_played_at TIMESTAMP,
         total_games INTEGER DEFAULT 0,
         best_score INTEGER DEFAULT 0,
         best_xp INTEGER DEFAULT 0,
         magic_link_token TEXT,
         magic_link_expiry TIMESTAMP)
    ''')
    
    # Create regional stats table
    c.execute('''
        CREATE TABLE IF NOT EXISTS regional_stats
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         region_key TEXT UNIQUE,
         country TEXT,
         region TEXT,
         total_games INTEGER DEFAULT 0,
         total_players INTEGER DEFAULT 0,
         combat_style_brave INTEGER DEFAULT 0,
         combat_style_cautious INTEGER DEFAULT 0,
         combat_style_balanced INTEGER DEFAULT 0,
         action_fight INTEGER DEFAULT 0,
         action_run INTEGER DEFAULT 0,
         action_rest INTEGER DEFAULT 0,
         action_search_alone INTEGER DEFAULT 0,
         action_get_help INTEGER DEFAULT 0,
         last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    
    # Create player achievements table
    c.execute('''
        CREATE TABLE IF NOT EXISTS player_achievements
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         player_name TEXT,
         achievement TEXT,
         achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         UNIQUE(player_name, achievement))
    ''')
    
    # Create player session stats table
    c.execute('''
        CREATE TABLE IF NOT EXISTS player_session_stats
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         player_name TEXT,
         session_id TEXT UNIQUE,
         first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         games_played INTEGER DEFAULT 0,
         total_score INTEGER DEFAULT 0,
         total_xp INTEGER DEFAULT 0,
         best_score INTEGER DEFAULT 0,
         best_xp INTEGER DEFAULT 0,
         turn_count INTEGER DEFAULT 0,
         treasures_found INTEGER DEFAULT 0,
         treasure_attempts INTEGER DEFAULT 0,
         combat_encounters INTEGER DEFAULT 0,
         combat_style TEXT DEFAULT 'balanced',
         last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    
    # Create game sessions table for persistent game state
    c.execute('''
        CREATE TABLE IF NOT EXISTS game_sessions
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         session_id TEXT UNIQUE,
         player_name TEXT,
         game_state TEXT,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         expiry TIMESTAMP)
    ''')
    
    conn.commit()
    conn.close()

def add_to_leaderboard(player_name: str, score: int, xp: int, victory_type: str, health: int):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Ensure player exists in players table first
        c.execute('SELECT name FROM players WHERE name = ?', (player_name,))
        player_exists = c.fetchone()
        
        if not player_exists:
            # Create player if they don't exist
            c.execute(
                'INSERT INTO players (name, last_played, created_at) VALUES (?, ?, ?)',
                (player_name, datetime.now().isoformat(), datetime.now().isoformat())
            )
            print(f"Created new player record for {player_name} in add_to_leaderboard")
            
        c.execute('''
            INSERT INTO leaderboard (player_name, score, xp, victory_type, health)
            VALUES (?, ?, ?, ?, ?)
        ''', (player_name, score, xp, victory_type, health))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def get_leaderboard(limit: int = 10) -> List[LeaderboardEntry]:
    entries = []
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT player_name, score, xp, victory_type, health, date
            FROM leaderboard
            ORDER BY xp DESC, score DESC
            LIMIT ?
        ''', (limit,))
        entries = [LeaderboardEntry(name, score, xp, victory_type, health, datetime.fromisoformat(date))
                  for name, score, xp, victory_type, health, date in c.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error in get_leaderboard: {e}")
    finally:
        conn.close()
    return entries

def create_magic_link(email: str) -> str:
    """Create a magic link token for email authentication"""
    token = secrets.token_urlsafe(32)
    expiry = datetime.now().timestamp() + 3600  # 1 hour expiry
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create or update user
    c.execute('''
        INSERT INTO users (email, magic_link_token, magic_link_expiry)
        VALUES (?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET
            magic_link_token = excluded.magic_link_token,
            magic_link_expiry = excluded.magic_link_expiry
    ''', (email, token, expiry))
    
    conn.commit()
    conn.close()
    
    return token

def verify_magic_link(token: str) -> tuple[bool, str]:
    """Verify a magic link token and return (success, email)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT email, magic_link_expiry 
        FROM users 
        WHERE magic_link_token = ?
    ''', (token,))
    
    result = c.fetchone()
    if not result:
        return False, ""
    
    email, expiry = result
    if datetime.now().timestamp() > expiry:
        return False, ""
    
    # Clear the used token
    c.execute('''
        UPDATE users 
        SET magic_link_token = NULL, 
            magic_link_expiry = NULL 
        WHERE email = ?
    ''', (email,))
    
    conn.commit()
    conn.close()
    
    return True, email

def update_user_stats(email: str, score: int, xp: int):
    """Update user's stats after a game"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        UPDATE users 
        SET last_played_at = CURRENT_TIMESTAMP,
            total_games = total_games + 1,
            best_score = MAX(best_score, ?),
            best_xp = MAX(best_xp, ?)
        WHERE email = ?
    ''', (score, xp, email))
    
    conn.commit()
    conn.close()

def update_regional_stats(region_key: str, country: str, region: str, player_name: str, 
                         combat_style: Optional[str] = None, action: Optional[str] = None):
    """Update regional statistics"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # First, try to insert a new region if it doesn't exist
        c.execute('''
            INSERT OR IGNORE INTO regional_stats (region_key, country, region)
            VALUES (?, ?, ?)
        ''', (region_key, country, region))
        
        # Update combat style if provided
        if combat_style:
            c.execute(f'''
                UPDATE regional_stats 
                SET combat_style_{combat_style} = combat_style_{combat_style} + 1,
                    last_updated = CURRENT_TIMESTAMP
                WHERE region_key = ?
            ''', (region_key,))
        
        # Update action count if provided
        if action:
            c.execute(f'''
                UPDATE regional_stats 
                SET action_{action} = action_{action} + 1,
                    last_updated = CURRENT_TIMESTAMP
                WHERE region_key = ?
            ''', (region_key,))
        
        # Update total games and players
        c.execute('''
            UPDATE regional_stats 
            SET total_games = total_games + 1,
                total_players = (
                    SELECT COUNT(DISTINCT player_name) 
                    FROM leaderboard 
                    WHERE player_name LIKE ?
                ),
                last_updated = CURRENT_TIMESTAMP
            WHERE region_key = ?
        ''', (f"%{player_name}%", region_key))
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in update_regional_stats: {e}")
    finally:
        conn.close()

def get_regional_stats(region_key: str) -> dict:
    """Get regional statistics"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''
            SELECT * FROM regional_stats WHERE region_key = ?
        ''', (region_key,))
        row = c.fetchone()
        if row:
            columns = [description[0] for description in c.description]
            return dict(zip(columns, row))
        return None
    except sqlite3.Error as e:
        print(f"Database error in get_regional_stats: {e}")
        return None
    finally:
        conn.close()

def update_player_achievement(player_name: str, achievement: str):
    """Record a player achievement"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Ensure player exists in players table first
        c.execute('SELECT name FROM players WHERE name = ?', (player_name,))
        player_exists = c.fetchone()
        
        if not player_exists:
            # Create player if they don't exist
            c.execute(
                'INSERT INTO players (name, last_played, created_at) VALUES (?, ?, ?)',
                (player_name, datetime.now().isoformat(), datetime.now().isoformat())
            )
            print(f"Created new player record for {player_name} in update_player_achievement")
            
        c.execute('''
            INSERT OR IGNORE INTO player_achievements (player_name, achievement)
            VALUES (?, ?)
        ''', (player_name, achievement))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in update_player_achievement: {e}")
    finally:
        conn.close()

def update_player_session_stats(player_name: str, session_id: str, stats_update: dict):
    """Update player session statistics"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Defensive code to handle string values
        if isinstance(stats_update, str):
            print(f"Warning: String passed to update_player_session_stats instead of dict: {stats_update}")
            # Convert string to a simple counter with value 1
            stats_update = {stats_update: 1}
        elif not isinstance(stats_update, dict):
            print(f"Warning: Non-dict passed to update_player_session_stats: {type(stats_update)}")
            return
        
        # Ensure player exists in players table first
        c.execute('SELECT name FROM players WHERE name = ?', (player_name,))
        player_exists = c.fetchone()
        
        if not player_exists:
            # Create player if they don't exist
            c.execute(
                'INSERT INTO players (name, last_played, created_at) VALUES (?, ?, ?)',
                (player_name, datetime.now().isoformat(), datetime.now().isoformat())
            )
            print(f"Created new player record for {player_name} in update_player_session_stats")
        
        # First, try to insert a new session if it doesn't exist
        c.execute('''
            INSERT OR IGNORE INTO player_session_stats (player_name, session_id)
            VALUES (?, ?)
        ''', (player_name, session_id))
        
        # Build the update query dynamically based on provided stats
        update_fields = []
        update_values = []
        for key, value in stats_update.items():
            if key in ['games_played', 'total_score', 'total_xp', 'best_score', 'best_xp', 
                      'turn_count', 'treasures_found', 'treasure_attempts', 'victory', 'game_over', 'combat_encounters']:
                update_fields.append(f"{key} = {key} + ?")
                update_values.append(value)
            elif key in ['combat_style']:
                update_fields.append(f"{key} = ?")
                update_values.append(value)
        
        if update_fields:
            update_fields.append("last_updated = CURRENT_TIMESTAMP")
            query = f'''
                UPDATE player_session_stats 
                SET {', '.join(update_fields)}
                WHERE player_name = ? AND session_id = ?
            '''
            c.execute(query, update_values + [player_name, session_id])
            
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in update_player_session_stats: {e}")
    finally:
        conn.close()

def get_player_session_stats(player_name: str, session_id: str) -> dict:
    """Get player session statistics"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        print(f"DEBUG DB: Trying to get session stats for player {player_name} with session_id {session_id}")
        c.execute('''
            SELECT * FROM player_session_stats 
            WHERE player_name = ? AND session_id = ?
        ''', (player_name, session_id))
        row = c.fetchone()
        if row:
            columns = [description[0] for description in c.description]
            result = dict(zip(columns, row))
            print(f"DEBUG DB: Found session stats: {result}")
            
            # Check if this is a brand new session with no activity
            if result.get('turn_count', 0) == 0 and result.get('games_played', 0) == 0:
                print(f"DEBUG DB: This appears to be a brand new session with no activity")
                return None
            
            return result
        
        # Try with just player_name if no exact match, but only for sessions
        # that aren't the current one (to prevent treating a new player as returning)
        print(f"DEBUG DB: No exact match, trying with just player_name: {player_name}")
        c.execute('''
            SELECT * FROM player_session_stats 
            WHERE player_name = ? AND session_id != ?
            ORDER BY last_updated DESC
            LIMIT 1
        ''', (player_name, session_id))
        row = c.fetchone()
        if row:
            columns = [description[0] for description in c.description]
            result = dict(zip(columns, row))
            print(f"DEBUG DB: Found player stats from previous session: {result}")
            return result
            
        print(f"DEBUG DB: No session stats found for player {player_name}")
        return None
    except sqlite3.Error as e:
        print(f"Database error in get_player_session_stats: {e}")
        return None
    finally:
        conn.close()

def get_game_state_from_db(session_id: str) -> Dict[str, Any]:
    """
    Retrieve game state from database for a given session ID
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get game state from database
        c.execute('''
            SELECT game_state 
            FROM game_sessions
            WHERE session_id = ? AND (expiry IS NULL OR expiry > CURRENT_TIMESTAMP)
        ''', (session_id,))
        
        result = c.fetchone()
        if result and result[0]:
            # Update last_updated timestamp
            c.execute('''
                UPDATE game_sessions
                SET last_updated = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (session_id,))
            conn.commit()
            
            # Parse and return the game state
            return json.loads(result[0])
        
        return {}
    except sqlite3.Error as e:
        print(f"Database error in get_game_state_from_db: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"JSON decode error in get_game_state_from_db: {e}")
        return {}
    finally:
        conn.close()

def save_game_state_to_db(session_id: str, player_name: str, state: Dict[str, Any], 
                         expiry_days: int = 30) -> bool:
    """
    Save game state to database for a given session ID
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Ensure player exists in players table first
        try:
            c.execute('SELECT name FROM players WHERE name = ?', (player_name,))
            player_exists = c.fetchone()
            
            if not player_exists:
                # Create player if they don't exist
                c.execute(
                    'INSERT INTO players (name, last_played, created_at) VALUES (?, ?, ?)',
                    (player_name, datetime.now().isoformat(), datetime.now().isoformat())
                )
                print(f"Created new player record for {player_name} in save_game_state_to_db")
        except sqlite3.Error as e:
            print(f"Warning in save_game_state_to_db when checking player: {e}")
            # Continue anyway - we can save game state even if we can't update player record
        
        # Convert state to JSON
        state_json = json.dumps(state)
        
        # Calculate expiry date
        expiry = (datetime.now() + timedelta(days=expiry_days)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Insert or update game state
        c.execute('''
            INSERT INTO game_sessions 
            (session_id, player_name, game_state, last_updated, expiry)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                player_name = excluded.player_name,
                game_state = excluded.game_state,
                last_updated = CURRENT_TIMESTAMP,
                expiry = excluded.expiry
        ''', (session_id, player_name, state_json, expiry))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in save_game_state_to_db: {e}")
        return False
    finally:
        conn.close()

def cleanup_expired_sessions(days_old: int = 30) -> int:
    """
    Remove expired game sessions older than specified days
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Calculate the cutoff date
        cutoff_date = (datetime.now() - timedelta(days=days_old)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Delete expired sessions
        c.execute('''
            DELETE FROM game_sessions
            WHERE expiry < CURRENT_TIMESTAMP OR
                  (expiry IS NULL AND last_updated < ?)
        ''', (cutoff_date,))
        
        deleted_count = c.rowcount
        conn.commit()
        return deleted_count
    except sqlite3.Error as e:
        print(f"Database error in cleanup_expired_sessions: {e}")
        return 0
    finally:
        conn.close()

# Ensure database is initialized at import time
init_db()