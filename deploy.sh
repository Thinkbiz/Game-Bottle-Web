#!/bin/bash

# Enable error handling
set -e

# Configuration
VPS="game-vps"
DEPLOY_PATH="/opt/docker-game"
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== Creating backup ==="
# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create backup on VPS and download it
ssh $VPS "cd $DEPLOY_PATH && tar -czf /tmp/game_backup_$TIMESTAMP.tar.gz data/game.db logs/*.log"
scp $VPS:/tmp/game_backup_$TIMESTAMP.tar.gz $BACKUP_DIR/
ssh $VPS "rm /tmp/game_backup_$TIMESTAMP.tar.gz"

echo "=== Deploying latest code ==="
# Push latest changes to the VPS
ssh $VPS "cd $DEPLOY_PATH && git fetch origin main && git reset --hard origin/main"

echo "=== Rebuilding and restarting containers ==="
# Rebuild and restart the containers
ssh $VPS "cd $DEPLOY_PATH && \
    docker compose -f docker-compose.prod.yml down && \
    docker compose -f docker-compose.prod.yml build --no-cache && \
    docker compose -f docker-compose.prod.yml up -d"

echo "=== Waiting for startup ==="
sleep 10

echo "=== Checking deployment ==="
# Check container status and logs
ssh $VPS "cd $DEPLOY_PATH && \
    echo '=== CONTAINER STATUS ===' && \
    docker ps -a && \
    echo '=== CONTAINER LOGS ===' && \
    docker compose -f docker-compose.prod.yml logs --tail=50"

echo "=== Deployment complete ===" 