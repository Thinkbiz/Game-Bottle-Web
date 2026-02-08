#!/usr/bin/env python3
"""
Script to backup the SQLite database file with rotation functionality.
This script can be run manually or scheduled using cron/systemd.
"""

import os
import sys
import shutil
import sqlite3
import time
from datetime import datetime
import glob
import logging
from typing import List, Optional

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import configuration
from config import DB_PATH, DB_BACKUP_DIR, LOG_DIR
from logger import get_logger

# Setup logging
logger = get_logger('backup')

def create_backup(backup_dir: str, db_path: str) -> Optional[str]:
    """
    Create a backup of the SQLite database.
    
    Args:
        backup_dir: Directory to store the backup
        db_path: Path to the SQLite database file
        
    Returns:
        Path to the created backup file or None if failed
    """
    try:
        # Ensure backup directory exists
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"game_db_backup_{timestamp}.sqlite"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Check if database file exists
        if not os.path.exists(db_path):
            logger.error(f"Database file not found at {db_path}")
            return None
        
        # Ensure database is valid before backup
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA integrity_check")
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Database integrity check failed: {e}")
            return None
        
        # Create backup
        logger.info(f"Creating backup of {db_path} to {backup_path}")
        shutil.copy2(db_path, backup_path)
        
        # Verify backup was created
        if os.path.exists(backup_path):
            logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
        else:
            logger.error("Backup creation failed")
            return None
    
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return None

def rotate_backups(backup_dir: str, max_backups: int = 7) -> int:
    """
    Rotate backups, keeping only the specified number of recent backups.
    
    Args:
        backup_dir: Directory containing backup files
        max_backups: Maximum number of backups to keep
        
    Returns:
        Number of deleted backup files
    """
    try:
        # Get list of backup files
        backup_pattern = os.path.join(backup_dir, "game_db_backup_*.sqlite")
        backup_files = sorted(glob.glob(backup_pattern))
        
        # If we have more backups than the maximum, delete the oldest ones
        files_to_delete = max(0, len(backup_files) - max_backups)
        
        if files_to_delete > 0:
            logger.info(f"Rotating backups, keeping {max_backups} most recent files")
            
            # Delete oldest backups
            for i in range(files_to_delete):
                try:
                    os.remove(backup_files[i])
                    logger.debug(f"Deleted old backup: {backup_files[i]}")
                except Exception as e:
                    logger.error(f"Error deleting backup {backup_files[i]}: {e}")
                    files_to_delete -= 1
            
            logger.info(f"Deleted {files_to_delete} old backup files")
            return files_to_delete
        else:
            logger.info(f"No backup rotation needed, {len(backup_files)} backups exist (max: {max_backups})")
            return 0
    
    except Exception as e:
        logger.error(f"Error rotating backups: {e}")
        return 0

def main():
    """Main backup function"""
    logger.info("Starting database backup process")
    
    # Create backup
    backup_path = create_backup(DB_BACKUP_DIR, DB_PATH)
    
    if not backup_path:
        logger.error("Backup failed")
        sys.exit(1)
    
    # Rotate backups
    rotated = rotate_backups(DB_BACKUP_DIR)
    
    logger.info("Backup process completed successfully")

if __name__ == "__main__":
    main() 