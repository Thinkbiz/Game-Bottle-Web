#!/bin/bash
# Deployment script for Game-Bottle-Web

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting deployment of Game-Bottle-Web...${NC}"
echo "============================================"

# Check if docker and docker-compose are installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}Error: docker-compose.prod.yml not found.${NC}"
    echo "Please run this script from the root directory of the project."
    exit 1
fi

# Get the latest code if in a git repository
if [ -d ".git" ]; then
    echo -e "${YELLOW}Pulling latest code from repository...${NC}"
    git pull
    echo -e "${GREEN}Successfully pulled latest code.${NC}"
fi

# Create necessary directories
echo -e "${YELLOW}Setting up directories...${NC}"
mkdir -p data logs

# Backup the database if it exists
if [ -f "data/game.db" ]; then
    echo -e "${YELLOW}Backing up existing database...${NC}"
    backup_filename="data/game.db.backup-$(date +%Y%m%d%H%M%S)"
    cp data/game.db "$backup_filename"
    echo -e "${GREEN}Database backed up to $backup_filename${NC}"
fi

# Build and start the containers in production mode
echo -e "${YELLOW}Building and starting Docker containers...${NC}"
docker-compose -f docker-compose.prod.yml up -d --build

# Wait a bit for the app to start
echo -e "${YELLOW}Waiting for application to start...${NC}"
sleep 10

# Check if the container is running and healthy
container_status=$(docker-compose -f docker-compose.prod.yml ps -q web | xargs docker inspect -f '{{.State.Health.Status}}')

if [ "$container_status" = "healthy" ]; then
    echo -e "${GREEN}✓ Application deployed successfully and is healthy!${NC}"
    echo -e "${GREEN}You can access the application at http://localhost:8000${NC}"
else
    echo -e "${RED}✗ Application may have issues. Please check the logs:${NC}"
    docker-compose -f docker-compose.prod.yml logs web
fi

# Print some helpful information
echo -e "\n${YELLOW}Deployment complete!${NC}"
echo -e "To view logs: ${GREEN}docker-compose -f docker-compose.prod.yml logs -f${NC}"
echo -e "To stop the application: ${GREEN}docker-compose -f docker-compose.prod.yml down${NC}"
echo "============================================" 