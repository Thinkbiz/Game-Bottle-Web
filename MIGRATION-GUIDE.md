# Game-Bottle-Web Migration Guide

This document outlines the migration from in-memory session management to SQLite-based persistence, along with other improvements.

## Migration Changes

The following key changes have been implemented:

1. **Session Management:** Game sessions are now stored in SQLite instead of in-memory dictionaries
2. **Configuration Management:** Centralized configuration in `config.py` with environment variable support
3. **Logging Enhancements:** Improved logging with JSON format and session context
4. **Database Backups:** Automated backup system with rotation
5. **Session Cleanup:** Automatic cleanup of expired sessions

## Running the Migration

To migrate existing data from in-memory storage to the database:

```bash
python migrate_to_db.py
```

This will:
1. Dump current in-memory game states to a JSON file in the data directory
2. Create the necessary database tables if they don't exist
3. Insert the game states into the database
4. Log the migration process to the logs directory

## New Configuration System

The application now uses a centralized configuration system in `config.py` with environment variable support. Key configuration options include:

- `DEVELOPMENT`: Set to 1 to enable development mode
- `DEBUG`: Set to 1 to enable debug mode
- `DB_PATH`: Database file path
- `LOG_DIR`: Log directory
- `SESSION_EXPIRY_DAYS`: Number of days before sessions expire

See `config.py` for all available options and their default values.

## Database Backups

The application now includes a database backup system. To manually create a backup:

```bash
python backup_db.py
```

By default, this will:
1. Create a backup of the database in the `DB_BACKUP_DIR` directory
2. Keep the 7 most recent backups
3. Log the backup process

To schedule regular backups, consider using cron or systemd timers:

```bash
# Example cron entry for daily backups at 2 AM
0 2 * * * cd /path/to/app && python backup_db.py
```

## Session Cleanup

The application now automatically cleans up expired sessions:

1. A background thread runs every 6 hours to remove expired sessions
2. Sessions expire after the number of days specified in `SESSION_EXPIRY_DAYS` (default: 30)
3. You can manually trigger cleanup by running:

```bash
from database import cleanup_expired_sessions
cleanup_expired_sessions(days=30)  # Remove sessions older than 30 days
```

## New Logging System

The application now uses a more robust logging system:

1. Logs are written to both files and stdout in JSON format
2. Session context is automatically added to logs
3. Separate loggers for different components (game, database, API, etc.)
4. Log rotation to prevent excessive disk usage

Log files are stored in the `LOG_DIR` directory and include:
- `game.log`: General game logs
- `game_state.log`: Game state transition logs
- `db.log`: Database operation logs
- `api.log`: API request logs
- `web.log`: Web server logs

## Compatibility Notes

- For backward compatibility, game states are still stored in-memory as well as in the database
- Client-side session handling has been updated to synchronize with server-side cookies
- For multi-instance deployments, further changes would be needed (not included in this migration)

## Future Considerations

Future improvements could include:
1. Moving to a proper ORM like SQLAlchemy for database access
2. Implementing Redis for session storage in multi-instance setups
3. Adding more detailed metrics and monitoring
4. Implementing proper user authentication