#!/bin/bash

# Create backup directory if it doesn't exist
mkdir -p db_backups

# Get current timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Copy the database file from the Docker volume
echo "Creating database backup..."
docker cp monsters-and-treasure:/app/data/game.db ./db_backups/game_${TIMESTAMP}.db

# Verify backup
if [ -f "./db_backups/game_${TIMESTAMP}.db" ]; then
    echo "Backup successful: game_${TIMESTAMP}.db"
    # Create a latest symlink
    ln -sf "./game_${TIMESTAMP}.db" "./db_backups/game_latest.db"
else
    echo "Backup failed!"
    exit 1
fi 