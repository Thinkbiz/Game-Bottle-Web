import sqlite3
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class GameState:
    player_name: str
    health: int
    score: int
    xp: int
    current_stage: str

@dataclass
class LeaderboardEntry:
    player_name: str
    score: int
    xp: int
    victory_type: str
    health: int
    date: datetime

def init_db():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    
    # Drop existing tables to start fresh
    c.execute('DROP TABLE IF EXISTS game_states')
    c.execute('DROP TABLE IF EXISTS leaderboard')
    
    # Existing game_states table
    c.execute('''
        CREATE TABLE IF NOT EXISTS game_states
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         player_name TEXT,
         health INTEGER,
         score INTEGER,
         xp INTEGER,
         current_stage TEXT,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    
    # New leaderboard table with health column
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
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO leaderboard (player_name, score, xp, victory_type, health)
        VALUES (?, ?, ?, ?, ?)
    ''', (player_name, score, xp, victory_type, health))
    conn.commit()
    conn.close()

def get_leaderboard(limit: int = 10) -> List[LeaderboardEntry]:
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('''
        SELECT player_name, score, xp, victory_type, health, date
        FROM leaderboard
        ORDER BY xp DESC, score DESC
        LIMIT ?
    ''', (limit,))
    entries = [LeaderboardEntry(name, score, xp, victory_type, health, datetime.fromisoformat(date))
              for name, score, xp, victory_type, health, date in c.fetchall()]
    conn.close()
    return entries 