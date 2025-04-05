import sqlite3
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
import os
import secrets
import hashlib

# Ensure data directory exists
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'game.db')

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
    
    # Drop existing tables to start fresh
    c.execute('DROP TABLE IF EXISTS leaderboard')
    
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
         combat_style TEXT DEFAULT 'balanced',
         last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    
    conn.commit()
    conn.close()

def migrate_db():
    """Add any missing columns to existing tables without dropping data"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Check if regional_stats table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='regional_stats'")
        if not c.fetchone():
            # Create regional_stats table if it doesn't exist
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
            print("Created regional_stats table")
        else:
            # Check for missing columns
            c.execute("PRAGMA table_info(regional_stats)")
            columns = [column[1] for column in c.fetchall()]
            
            missing_columns = {
                'total_games': 'INTEGER DEFAULT 0',
                'total_players': 'INTEGER DEFAULT 0',
                'combat_style_brave': 'INTEGER DEFAULT 0',
                'combat_style_cautious': 'INTEGER DEFAULT 0',
                'combat_style_balanced': 'INTEGER DEFAULT 0',
                'action_fight': 'INTEGER DEFAULT 0',
                'action_run': 'INTEGER DEFAULT 0',
                'action_rest': 'INTEGER DEFAULT 0',
                'action_search_alone': 'INTEGER DEFAULT 0',
                'action_get_help': 'INTEGER DEFAULT 0'
            }
            
            for column, type_def in missing_columns.items():
                if column not in columns:
                    try:
                        c.execute(f'''
                            ALTER TABLE regional_stats
                            ADD COLUMN {column} {type_def}
                        ''')
                        print(f"Added {column} column to regional_stats table")
                    except sqlite3.Error as e:
                        print(f"Error adding column {column}: {e}")
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

# Initialize database if it doesn't exist
if not os.path.exists(DB_PATH):
    init_db()
else:
    # Run migrations on existing database
    migrate_db()

def add_to_leaderboard(player_name: str, score: int, xp: int, victory_type: str, health: int):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
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

def update_regional_stats(region_key: str, country: str, region: str, stats_update: dict):
    """Update regional statistics with error handling and column validation"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # First check if the region exists
        c.execute('''
            INSERT OR IGNORE INTO regional_stats 
            (region_key, country, region, total_games)
            VALUES (?, ?, ?, 0)
        ''', (region_key, country, region))
        
        # Build update query dynamically based on provided stats
        valid_columns = [
            'total_games', 'total_players', 
            'combat_style_brave', 'combat_style_cautious', 'combat_style_balanced',
            'action_fight', 'action_run', 'action_rest', 
            'action_search_alone', 'action_get_help'
        ]
        
        # Filter out invalid columns
        update_cols = {k: v for k, v in stats_update.items() if k in valid_columns}
        
        if update_cols:
            set_clause = ', '.join([f"{k} = {k} + ?" for k in update_cols.keys()])
            query = f'''
                UPDATE regional_stats 
                SET {set_clause},
                    last_updated = CURRENT_TIMESTAMP
                WHERE region_key = ?
            '''
            
            # Execute update with all parameters
            c.execute(query, list(update_cols.values()) + [region_key])
            
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error in update_regional_stats: {e}")
        conn.rollback()
        return False
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
                      'turn_count', 'treasures_found', 'treasure_attempts']:
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
        c.execute('''
            SELECT * FROM player_session_stats 
            WHERE player_name = ? AND session_id = ?
        ''', (player_name, session_id))
        row = c.fetchone()
        if row:
            columns = [description[0] for description in c.description]
            return dict(zip(columns, row))
        return None
    except sqlite3.Error as e:
        print(f"Database error in get_player_session_stats: {e}")
        return None
    finally:
        conn.close()