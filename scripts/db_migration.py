#!/usr/bin/env python3
import os
import sys
import sqlite3
import tarfile
import shutil
import logging
import argparse
from datetime import datetime
from typing import Optional, Tuple, List, Dict
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/migration.log')
    ]
)
logger = logging.getLogger(__name__)

# Database schema definitions
SCHEMA_DEFINITIONS = {
    'players': '''
        CREATE TABLE IF NOT EXISTS players (
            name TEXT PRIMARY KEY,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_played TEXT,
            total_games INTEGER DEFAULT 0,
            total_victories INTEGER DEFAULT 0
        )
    ''',
    'game_states': '''
        CREATE TABLE IF NOT EXISTS game_states (
            session_id TEXT PRIMARY KEY,
            player_name TEXT,
            state TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT,
            FOREIGN KEY (player_name) REFERENCES players(name)
        )
    ''',
    'leaderboard': '''
        CREATE TABLE IF NOT EXISTS leaderboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            score INTEGER,
            xp INTEGER,
            victory_type TEXT,
            health INTEGER,
            achieved_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_name) REFERENCES players(name)
        )
    ''',
    'player_session_stats': '''
        CREATE TABLE IF NOT EXISTS player_session_stats (
            player_name TEXT,
            session_id TEXT,
            games_played INTEGER DEFAULT 0,
            combat_encounters INTEGER DEFAULT 0,
            treasures_found INTEGER DEFAULT 0,
            traps_survived INTEGER DEFAULT 0,
            best_score INTEGER DEFAULT 0,
            victory INTEGER DEFAULT 0,
            game_over INTEGER DEFAULT 0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player_name, session_id),
            FOREIGN KEY (player_name) REFERENCES players(name)
        )
    ''',
    'regional_stats': '''
        CREATE TABLE IF NOT EXISTS regional_stats (
            region_key TEXT PRIMARY KEY,
            country TEXT,
            region TEXT,
            total_players INTEGER DEFAULT 0,
            active_players INTEGER DEFAULT 0,
            avg_score REAL DEFAULT 0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    'achievements': '''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            achievement TEXT,
            achieved_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_name) REFERENCES players(name)
        )
    '''
}

class DatabaseMigration:
    def __init__(self, backup_path: str, temp_dir: str = 'temp_migration'):
        self.backup_path = backup_path
        self.temp_dir = temp_dir
        self.original_db = 'data/game.db'
        self.backup_db = None
        self.tables_to_validate = list(SCHEMA_DEFINITIONS.keys())

    def create_backup(self) -> bool:
        """Create a backup of the current database before migration"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'data/game_pre_migration_{timestamp}.db'
            if os.path.exists(self.original_db):
                shutil.copy2(self.original_db, backup_name)
                logger.info(f"Created backup at {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False

    def extract_backup(self) -> bool:
        """Extract the backup tarfile to temporary directory"""
        try:
            os.makedirs(self.temp_dir, exist_ok=True)
            with tarfile.open(self.backup_path, 'r:gz') as tar:
                tar.extractall(path=self.temp_dir)
            self.backup_db = os.path.join(self.temp_dir, 'data/game.db')
            return os.path.exists(self.backup_db)
        except Exception as e:
            logger.error(f"Failed to extract backup: {e}")
            return False

    def initialize_schema(self, db_path: str) -> bool:
        """Initialize the database schema if needed"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Create each table if it doesn't exist
            for table_name, schema in SCHEMA_DEFINITIONS.items():
                cursor.execute(schema)
            
            conn.commit()
            logger.info(f"Schema initialized successfully for {db_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()

    def validate_backup_db(self) -> Tuple[bool, Dict]:
        """Validate the backup database structure and data"""
        validation_results = {
            'tables_present': False,
            'data_integrity': False,
            'row_counts': {},
            'errors': []
        }

        try:
            conn = sqlite3.connect(self.backup_db)
            cursor = conn.cursor()

            # Initialize schema if needed
            self.initialize_schema(self.backup_db)

            # Check if all required tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            missing_tables = set(self.tables_to_validate) - existing_tables
            
            if missing_tables:
                validation_results['errors'].append(f"Missing tables: {missing_tables}")
                return False, validation_results

            validation_results['tables_present'] = True

            # Get row counts and validate basic data integrity
            for table in self.tables_to_validate:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                validation_results['row_counts'][table] = count

                # Basic data validation for each table
                if table == 'players':
                    cursor.execute("SELECT COUNT(*) FROM players WHERE name IS NULL")
                    if cursor.fetchone()[0] > 0:
                        validation_results['errors'].append(f"Found players with NULL names")

                elif table == 'game_states':
                    cursor.execute("SELECT COUNT(*) FROM game_states WHERE state IS NULL")
                    if cursor.fetchone()[0] > 0:
                        validation_results['errors'].append(f"Found game states with NULL state data")

            validation_results['data_integrity'] = len(validation_results['errors']) == 0
            return validation_results['data_integrity'], validation_results

        except Exception as e:
            validation_results['errors'].append(f"Validation error: {str(e)}")
            return False, validation_results
        finally:
            if 'conn' in locals():
                conn.close()

    def perform_migration(self) -> bool:
        """Perform the actual database migration"""
        try:
            # Stop the game server if it's running
            # This should be handled by the deployment script
            
            # Initialize schema in the backup database
            if not self.initialize_schema(self.backup_db):
                raise Exception("Failed to initialize schema in backup database")
            
            # Copy the validated backup database to the target location
            shutil.copy2(self.backup_db, self.original_db)
            
            # Verify the copy was successful
            if not os.path.exists(self.original_db):
                raise Exception("Failed to copy backup database to target location")
            
            # Verify the copied database is readable and has the correct schema
            conn = sqlite3.connect(self.original_db)
            cursor = conn.cursor()
            
            # Verify schema
            for table in self.tables_to_validate:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
            
            # Get some basic stats
            cursor.execute("SELECT COUNT(*) FROM players")
            player_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM game_states")
            state_count = cursor.fetchone()[0]
            
            logger.info(f"Migration successful. Database contains {player_count} players and {state_count} active game states")
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    def rollback(self, pre_migration_backup: str) -> bool:
        """Rollback to the pre-migration state"""
        try:
            if os.path.exists(pre_migration_backup):
                shutil.copy2(pre_migration_backup, self.original_db)
                logger.info("Successfully rolled back to pre-migration state")
                return True
            else:
                logger.error("Pre-migration backup not found")
                return False
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def cleanup(self):
        """Clean up temporary files and directories"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

def main():
    parser = argparse.ArgumentParser(description='Database Migration Tool')
    parser.add_argument('backup_file', help='Path to the backup file to restore')
    parser.add_argument('--dry-run', action='store_true', help='Validate backup without performing migration')
    parser.add_argument('--force-schema', action='store_true', help='Force schema initialization even if tables exist')
    args = parser.parse_args()

    if not os.path.exists(args.backup_file):
        logger.error(f"Backup file not found: {args.backup_file}")
        sys.exit(1)

    migration = DatabaseMigration(args.backup_file)

    # Create pre-migration backup
    if not migration.create_backup():
        logger.error("Failed to create pre-migration backup")
        sys.exit(1)

    # Extract and validate backup
    if not migration.extract_backup():
        logger.error("Failed to extract backup")
        sys.exit(1)

    # Validate backup database
    is_valid, validation_results = migration.validate_backup_db()
    logger.info("Validation Results:")
    logger.info(json.dumps(validation_results, indent=2))

    if not is_valid and not args.force_schema:
        logger.error("Backup validation failed")
        migration.cleanup()
        sys.exit(1)

    if args.dry_run:
        logger.info("Dry run completed successfully")
        migration.cleanup()
        sys.exit(0)

    # Perform migration
    if migration.perform_migration():
        logger.info("Migration completed successfully")
        migration.cleanup()
    else:
        logger.error("Migration failed")
        # Attempt rollback
        pre_migration_backup = f'data/game_pre_migration_{datetime.now().strftime("%Y%m%d")}_*.db'
        if migration.rollback(pre_migration_backup):
            logger.info("Rollback successful")
        else:
            logger.error("Rollback failed")
        migration.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main() 