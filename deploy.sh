#!/bin/bash

# Enable error handling
set -e

# Configuration
DEPLOY_PATH="/root/game-bottle-web"
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== Creating backup ==="
# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create backup on VPS and download it
ssh game-vps "cd $DEPLOY_PATH && \
    mkdir -p logs && \
    touch logs/.keep && \
    tar -czf /tmp/game_backup_$TIMESTAMP.tar.gz data/game.db logs/ || true"
scp game-vps:/tmp/game_backup_$TIMESTAMP.tar.gz $BACKUP_DIR/
ssh game-vps "rm /tmp/game_backup_$TIMESTAMP.tar.gz"

echo "=== Deploying latest code ==="
# Push latest changes to the VPS
ssh game-vps "cd $DEPLOY_PATH && git fetch origin production && git reset --hard origin/production"

echo "=== Rebuilding and restarting containers ==="
# Rebuild and restart the containers
ssh game-vps "cd $DEPLOY_PATH && \
    docker compose -f docker-compose.prod.yml down && \
    docker compose -f docker-compose.prod.yml build --no-cache && \
    docker compose -f docker-compose.prod.yml up -d"

echo "=== Waiting for startup ==="
sleep 10

echo "=== Checking deployment ==="
# Check container status and logs
ssh game-vps "cd $DEPLOY_PATH && \
    echo '=== CONTAINER STATUS ===' && \
    docker ps -a && \
    echo '=== CONTAINER LOGS ===' && \
    docker compose -f docker-compose.prod.yml logs --tail=50"

echo "=== Deployment complete ===" 