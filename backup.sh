#!/bin/bash
# Game-Bottle-Web Database Backup Script

# Configuration
VPS_USER="root"
VPS_HOST="167.88.39.165"
VPS_PORT="22"
REMOTE_DIR="/var/www/game-bottle-web"
BACKUP_DIR="./backups"
APP_NAME="game-bottle-web"
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILENAME="${APP_NAME}_backup_${DATE}.db"
KEEP_DAYS=30  # Number of days to keep backups

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Game-Bottle-Web Database Backup Script ===${NC}"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Connect to the VPS and create a database backup
echo -e "\n${GREEN}Creating database backup...${NC}"
ssh -p $VPS_PORT $VPS_USER@$VPS_HOST "cd $REMOTE_DIR && sqlite3 data/game.db .dump" > "$BACKUP_DIR/${BACKUP_FILENAME}.sql"

# Check if the backup was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Backup created successfully: ${BACKUP_FILENAME}.sql${NC}"
    
    # Compress the backup
    echo -e "${GREEN}Compressing backup...${NC}"
    gzip "$BACKUP_DIR/${BACKUP_FILENAME}.sql"
    
    echo -e "${GREEN}Backup compressed: ${BACKUP_FILENAME}.sql.gz${NC}"
    
    # Clean up old backups
    echo -e "${GREEN}Cleaning up backups older than $KEEP_DAYS days...${NC}"
    find $BACKUP_DIR -name "${APP_NAME}_backup_*.sql.gz" -mtime +$KEEP_DAYS -delete
    
    echo -e "\n${GREEN}Backup process completed successfully!${NC}"
    echo "Backup location: $BACKUP_DIR/${BACKUP_FILENAME}.sql.gz"
else
    echo -e "${RED}Backup failed!${NC}"
    exit 1
fi 