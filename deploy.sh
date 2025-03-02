#!/bin/bash
# Game-Bottle-Web Deployment Script

# Configuration
VPS_HOST="gamebottle"  # Use SSH config entry instead of explicit details
REMOTE_DIR="/var/www/game-bottle-web"
APP_NAME="game-bottle-web"
DOMAIN="nowmakefunthings.com"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Game-Bottle-Web Deployment Script ===${NC}"
echo "This script will deploy the application to your VPS."

# Check if VPS key exists
if [ ! -f ~/.ssh/vps_key.pub ]; then
    echo -e "${RED}SSH VPS key not found. Please make sure ~/.ssh/vps_key.pub exists.${NC}"
    exit 1
fi

# Step 1 is no longer needed - we've already set up SSH key authentication
echo -e "\n${GREEN}Step 1: SSH key authentication already set up${NC}"

# Step 2: Create a deployment package
echo -e "\n${GREEN}Step 2: Creating deployment package${NC}"
DEPLOY_DIR="deploy"
mkdir -p $DEPLOY_DIR

# Copy necessary files
echo "Copying application files..."
cp -r *.py $DEPLOY_DIR/
cp -r views $DEPLOY_DIR/
cp -r static $DEPLOY_DIR/
cp -r infrastructure $DEPLOY_DIR/
cp requirements.txt $DEPLOY_DIR/
cp docker-compose.yml $DEPLOY_DIR/
cp Dockerfile $DEPLOY_DIR/

# Create directories that need to exist
mkdir -p $DEPLOY_DIR/data
mkdir -p $DEPLOY_DIR/logs

# Create a simple README
cat > $DEPLOY_DIR/README.md << EOF
# Game-Bottle-Web

A web-based adventure game with database persistence.

## Setup

1. Install dependencies: \`pip install -r requirements.txt\`
2. Initialize the database: \`python -c "from database import init_db; init_db()"\`
3. Start the application: \`python app.py\`

## Docker Setup

1. Build and start with Docker Compose: \`docker-compose up -d\`
EOF

# Create a tar archive
echo "Creating archive..."
tar -czf ${APP_NAME}.tar.gz -C $DEPLOY_DIR .
rm -rf $DEPLOY_DIR

# Step 3: Copy files to server
echo -e "\n${GREEN}Step 3: Copying files to server${NC}"
ssh $VPS_HOST "mkdir -p $REMOTE_DIR"
scp ${APP_NAME}.tar.gz $VPS_HOST:$REMOTE_DIR/

# Step 4: Set up the server
echo -e "\n${GREEN}Step 4: Setting up the server${NC}"
ssh $VPS_HOST << EOF
    cd $REMOTE_DIR
    tar -xzf ${APP_NAME}.tar.gz
    rm ${APP_NAME}.tar.gz
    
    # Install dependencies
    echo "Installing dependencies..."
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-venv nginx
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install gunicorn
    
    # Initialize the database
    python -c "from database import init_db; init_db()"
    
    # Set up SSL directories
    echo "Setting up SSL directories..."
    sudo mkdir -p /etc/letsencrypt/live/${DOMAIN}
    sudo chmod 755 /etc/letsencrypt/live/${DOMAIN}
    
    # Set up Nginx
    echo "Setting up Nginx..."
    sudo cp infrastructure/nginx/game.conf /etc/nginx/sites-available/${APP_NAME}
    sudo ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl restart nginx
    
    # Set up systemd service
    echo "Setting up systemd service..."
    cat > ${APP_NAME}.service << EOFS
[Unit]
Description=Game Bottle Web Application
After=network.target

[Service]
User=root
WorkingDirectory=$REMOTE_DIR
ExecStart=$REMOTE_DIR/venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always
RestartSec=5
Environment="PATH=$REMOTE_DIR/venv/bin"

[Install]
WantedBy=multi-user.target
EOFS
    
    sudo mv ${APP_NAME}.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable ${APP_NAME}
    sudo systemctl start ${APP_NAME}
    
    echo "Deployment completed!"
EOF

# Clean up
rm ${APP_NAME}.tar.gz

echo -e "\n${GREEN}Deployment completed successfully!${NC}"
echo -e "${YELLOW}NOTE: SSL certificates can be uploaded using the upload-ssl.sh script:${NC}"
echo "./upload-ssl.sh"
echo -e "\nYour application should now be running at https://${DOMAIN}"
echo "To check the status: ssh $VPS_HOST 'sudo systemctl status ${APP_NAME}'" 