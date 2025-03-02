#!/bin/bash

# Configuration
VPS_HOST="gamebottle"
APP_NAME="game-bottle-web"
DEPLOY_DIR="/opt/game-bottle-web"

echo "=== ${APP_NAME} Container Deployment Script ==="
echo "This script will deploy the containerized application to your VPS."

# Determine project root directory (where this script is located)
PROJECT_ROOT="$(pwd)"

echo "Step 1: Preparing clean deployment files"
# For basic cleanup, remove obvious Mac files locally
find . -name ".DS_Store" -type f -delete
find . -name "._*" -type f -delete

# Create archive of all relevant files
echo "Creating archive..."
tar -cf game-bottle-web.tar \
    *.py \
    requirements.txt \
    Dockerfile.prod \
    docker-compose.prod.yml \
    scripts \
    static \
    views \
    data \
    gunicorn.conf.py

echo "Step 2: Transferring files to server for processing"
# Copy archive and key files to server
scp game-bottle-web.tar ${VPS_HOST}:/tmp/
scp docker-compose.prod.yml ${VPS_HOST}:/tmp/
scp Dockerfile.prod ${VPS_HOST}:/tmp/

echo "Step 3: Server-side processing and container setup"
# Connect to VPS and set up the application
ssh ${VPS_HOST} << EOF
  echo "Cleaning up previous files"
  rm -rf ~/game-bottle-web
  mkdir -p ~/game-bottle-web
  
  echo "Extracting and processing files on Linux server"
  # Extract on Linux system which doesn't preserve Mac attributes
  tar -xf /tmp/game-bottle-web.tar -C ~/game-bottle-web
  
  # Copy key files
  cp /tmp/docker-compose.prod.yml ~/game-bottle-web/
  cp /tmp/Dockerfile.prod ~/game-bottle-web/
  
  echo "Removing any potentially problematic files"
  # Secondary cleanup (just to be safe)
  find ~/game-bottle-web -name "._*" -type f -delete
  find ~/game-bottle-web -name ".DS_Store" -type f -delete
  find ~/game-bottle-web -name ".AppleDouble" -type d -exec rm -rf {} \; 2>/dev/null || true
  find ~/game-bottle-web -name "__MACOSX" -type d -exec rm -rf {} \; 2>/dev/null || true
  find ~/game-bottle-web -name ".localized" -type f -delete
  
  # Ensure critical directories exist
  mkdir -p ~/game-bottle-web/logs ~/game-bottle-web/data
  
  # Setup static files for Nginx
  echo "Setting up static files for Nginx"
  sudo mkdir -p /var/www/game-bottle-web/static
  sudo rm -rf /var/www/game-bottle-web/static/*
  sudo cp -r ~/game-bottle-web/static/* /var/www/game-bottle-web/static/ 2>/dev/null || true
  sudo find /var/www/game-bottle-web/static -type d -exec chmod 755 {} \;
  sudo find /var/www/game-bottle-web/static -type f -exec chmod 644 {} \;
  sudo chown -R www-data:www-data /var/www/game-bottle-web/static
  
  # Set proper permissions in the app directory
  echo "Setting permissions"
  find ~/game-bottle-web -type d -exec chmod 755 {} \;
  find ~/game-bottle-web -type f -exec chmod 644 {} \;
  find ~/game-bottle-web/scripts -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
  
  # Build and start container
  echo "Building and starting container"
  cd ~/game-bottle-web
  # Stop any previous containers
  docker compose -f docker-compose.prod.yml down || true
  # Remove previous images to force rebuild
  docker rmi game-bottle-web-web || true
  # Rebuild and start
  docker compose -f docker-compose.prod.yml up -d --build
  
  # Cleanup temp files
  rm -f /tmp/game-bottle-web.tar
EOF

echo "Step 4: Checking Nginx configuration"
# Check Nginx configuration and reload to apply changes
ssh ${VPS_HOST} "sudo nginx -t && sudo systemctl reload nginx"

echo "Step 5: Waiting for container startup (10 seconds)"
# Give the container time to start up
sleep 10

echo "Step 6: Checking deployment"
# Check if container is running
ssh ${VPS_HOST} "docker ps -a --filter 'name=game-bottle-web'"

# Check if application is healthy
HEALTH_CHECK=$(ssh ${VPS_HOST} "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health" || echo "Failed")
if [ "$HEALTH_CHECK" == "200" ]; then
  echo "Health check passed!"
else
  echo "Health check failed!"
  echo "Checking container logs:"
  ssh ${VPS_HOST} "docker logs \$(docker ps -q --filter name=game-bottle-web-web)"
fi

echo
echo "Deployment completed!"
echo "Your application should now be running at https://nowmakefunthings.com"
echo "To check container logs: ssh ${VPS_HOST} 'docker logs \$(docker ps -q --filter name=game-bottle-web-web)'" 