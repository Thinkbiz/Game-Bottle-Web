#!/usr/bin/env python3
"""
Database Import Script for Game-Bottle-Web

This script imports a SQLite database backup into the Docker container's
data volume. It validates the database structure before importing.
"""

import os
import sys
import shutil
import sqlite3
from datetime import datetime

def check_db_structure(db_path):
    """Verify the database has the expected tables"""
    required_tables = [
        "leaderboard", 
        "regional_stats", 
        "player_achievements", 
        "player_session_stats"
    ]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Check if all required tables exist
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"ERROR: The following tables are missing: {', '.join(missing_tables)}")
            return False
            
        print("Database structure looks valid")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to check database structure: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def import_database(source_path, destination_dir="./data"):
    """Import database from backup to the Docker data directory"""
    # Create destination directory if it doesn't exist
    os.makedirs(destination_dir, exist_ok=True)
    
    # Target path for the imported database
    destination_path = os.path.join(destination_dir, "game.db")
    
    # Create backup of existing DB if it exists
    if os.path.exists(destination_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{destination_path}.{timestamp}.bak"
        print(f"Creating backup of existing database: {backup_path}")
        shutil.copy2(destination_path, backup_path)
    
    # Check if source database is valid
    if not check_db_structure(source_path):
        print("Aborting import due to validation errors")
        return False
    
    # Copy the database
    try:
        print(f"Importing database from {source_path} to {destination_path}")
        shutil.copy2(source_path, destination_path)
        print("Database import completed successfully")
        return True
    except Exception as e:
        print(f"ERROR: Failed to import database: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python db_import.py <path_to_backup_db> [destination_directory]")
        sys.exit(1)
    
    source_db = sys.argv[1]
    dest_dir = sys.argv[2] if len(sys.argv) > 2 else "./data"
    
    if not os.path.exists(source_db):
        print(f"ERROR: Source database {source_db} does not exist")
        sys.exit(1)
    
    success = import_database(source_db, dest_dir)
    sys.exit(0 if success else 1) 