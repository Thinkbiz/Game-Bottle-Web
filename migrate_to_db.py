#!/usr/bin/env python3
"""
Migration script to transition game state from in-memory to database storage.
This script should be run once to migrate existing game state data into the SQLite database.
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import configuration
from config import DB_PATH, LOG_DIR, SESSION_EXPIRY_DAYS
from database import init_db
from logger import get_logger

# Setup logging
logger = get_logger('migration')

def migrate_game_states(game_states_dump_path: str) -> int:
    """
    Migrate game states from a JSON dump file to the database.
    
    Args:
        game_states_dump_path: Path to the JSON dump file containing game states
        
    Returns:
        Number of game states migrated
    """
    try:
        # Load the game states from the JSON dump
        logger.info(f"Loading game states from {game_states_dump_path}")
        with open(game_states_dump_path, 'r') as f:
            game_states = json.load(f)
        
        logger.info(f"Found {len(game_states)} game states to migrate")
        
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Calculate expiry date
        expiry_date = datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)
        expiry_str = expiry_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Prepare SQL statement
        sql = """
        INSERT OR REPLACE INTO game_sessions 
        (session_id, player_name, game_state, created_at, last_updated, expiry)
        VALUES (?, ?, ?, datetime('now'), datetime('now'), ?)
        """
        
        migrated_count = 0
        
        # Migrate each game state
        for session_id, state in game_states.items():
            try:
                # Extract player name
                player_name = state.get('player_name', 'anonymous')
                
                # Serialize the game state
                state_json = json.dumps(state)
                
                # Insert into database
                cursor.execute(sql, (session_id, player_name, state_json, expiry_str))
                migrated_count += 1
                
                logger.debug(f"Migrated game state for session {session_id}, player {player_name}")
            except Exception as e:
                logger.error(f"Error migrating game state for session {session_id}: {e}")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully migrated {migrated_count} game states to the database")
        return migrated_count
    
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        return 0

def create_game_states_dump(app_module_path: str) -> Optional[str]:
    """
    Create a JSON dump of the in-memory game states from the app module.
    
    Args:
        app_module_path: Path to the web_game.py file
        
    Returns:
        Path to the created dump file or None if failed
    """
    try:
        # First make sure the target directory exists
        os.makedirs(os.path.join(script_dir, 'data'), exist_ok=True)
        
        # Import the module dynamically
        sys.path.insert(0, os.path.dirname(app_module_path))
        import web_game
        
        # Get the game states
        game_states = web_game.game_states
        
        if not game_states:
            logger.warning("No game states found in memory")
            return None
        
        # Create dump file
        dump_path = os.path.join(script_dir, 'data', f'game_states_dump_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        # Write the game states to the dump file
        with open(dump_path, 'w') as f:
            json.dump(game_states, f, indent=2)
        
        logger.info(f"Created game states dump at {dump_path} with {len(game_states)} states")
        return dump_path
    
    except Exception as e:
        logger.error(f"Error creating game states dump: {e}")
        return None

def main():
    """Main migration function"""
    logger.info("Starting migration from in-memory to database storage")
    
    # Initialize the database to ensure tables exist
    init_db()
    
    # Path to the web_game.py file
    app_module_path = os.path.join(script_dir, 'web_game.py')
    
    # Create a dump of the current game states
    dump_path = create_game_states_dump(app_module_path)
    
    if not dump_path:
        logger.error("Failed to create game states dump, migration aborted")
        sys.exit(1)
    
    # Migrate the game states
    migrated_count = migrate_game_states(dump_path)
    
    if migrated_count > 0:
        logger.info(f"Migration completed successfully. Migrated {migrated_count} game states.")
    else:
        logger.warning("Migration completed but no game states were migrated.")

if __name__ == "__main__":
    main() 