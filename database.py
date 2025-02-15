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
    
    conn.commit()
    conn.close()

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