import sqlite3
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
import os

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
    
    # Only keep the leaderboard table
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