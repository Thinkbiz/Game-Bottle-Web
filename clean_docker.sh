#!/bin/bash

# Enable error handling
set -e

# Configuration
VPS="game-vps"
DEPLOY_PATH="/opt/docker-game"
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== Creating backup of critical data ==="
ssh $VPS "cd $DEPLOY_PATH && \
    tar -czf /tmp/critical_backup_$TIMESTAMP.tar.gz \
    data/game.db \
    logs/*.log \
    /etc/letsencrypt/live/nowmakefunthings.com/* \
    /etc/letsencrypt/archive/nowmakefunthings.com/*"

echo "=== Downloading backup ==="
mkdir -p $BACKUP_DIR
scp $VPS:/tmp/critical_backup_$TIMESTAMP.tar.gz $BACKUP_DIR/
ssh $VPS "rm /tmp/critical_backup_$TIMESTAMP.tar.gz"

echo "=== Stopping Docker services ==="
ssh $VPS "systemctl stop docker.service docker.socket || true"

echo "=== Removing Docker ==="
ssh $VPS "apt-get purge -y docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-ce-rootless-extras"

echo "=== Cleaning Docker artifacts ==="
ssh $VPS "rm -rf /var/lib/docker /etc/docker /var/run/docker.sock"

echo "=== Installing fresh Docker ==="
ssh $VPS "apt-get update && \
    apt-get install -y ca-certificates curl gnupg && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \$(. /etc/os-release && echo \$VERSION_CODENAME) stable\" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"

echo "=== Verifying Docker installation ==="
ssh $VPS "docker --version && docker compose version"

echo "=== Cleanup complete ==="
echo "Backup saved to: $BACKUP_DIR/critical_backup_$TIMESTAMP.tar.gz" 