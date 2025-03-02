#!/bin/bash
# Script to set up SSL with Let's Encrypt

# Configuration
VPS_USER="root"
VPS_HOST="167.88.39.165"
VPS_PORT="22"  # Add this line to specify SSH port
DOMAIN="your_domain.com"  # We'll update this later when we have a domain
APP_NAME="game-bottle-web"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Setting up SSL for $DOMAIN ===${NC}"

# Connect to the VPS and set up SSL
ssh -p $VPS_PORT $VPS_USER@$VPS_HOST << EOF
    echo -e "${GREEN}Installing Certbot...${NC}"
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
    
    echo -e "${GREEN}Obtaining SSL certificate...${NC}"
    sudo certbot --nginx -d $DOMAIN
    
    echo -e "${GREEN}Updating Nginx configuration...${NC}"
    # Uncomment SSL configuration in the Nginx config file
    sudo sed -i 's/# listen 443 ssl;/listen 443 ssl;/g' /etc/nginx/sites-available/$APP_NAME
    sudo sed -i "s|# ssl_certificate /etc/letsencrypt/live/your_domain.com/fullchain.pem;|ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;|g" /etc/nginx/sites-available/$APP_NAME
    sudo sed -i "s|# ssl_certificate_key /etc/letsencrypt/live/your_domain.com/privkey.pem;|ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;|g" /etc/nginx/sites-available/$APP_NAME
    sudo sed -i 's/# include \/etc\/letsencrypt\/options-ssl-nginx.conf;/include \/etc\/letsencrypt\/options-ssl-nginx.conf;/g' /etc/nginx/sites-available/$APP_NAME
    sudo sed -i 's/# ssl_dhparam \/etc\/letsencrypt\/ssl-dhparams.pem;/ssl_dhparam \/etc\/letsencrypt\/ssl-dhparams.pem;/g' /etc/nginx/sites-available/$APP_NAME
    
    # Uncomment HSTS header
    sudo sed -i 's/# add_header Strict-Transport-Security/add_header Strict-Transport-Security/g' /etc/nginx/sites-available/$APP_NAME
    
    # Uncomment HTTP to HTTPS redirect
    sudo sed -i 's/# server {/server {/g' /etc/nginx/sites-available/$APP_NAME
    sudo sed -i 's/#     listen 80;/    listen 80;/g' /etc/nginx/sites-available/$APP_NAME
    sudo sed -i "s/#     server_name your_domain.com;/    server_name $DOMAIN;/g" /etc/nginx/sites-available/$APP_NAME
    sudo sed -i 's/#     /    /g' /etc/nginx/sites-available/$APP_NAME
    sudo sed -i 's/# }/}/g' /etc/nginx/sites-available/$APP_NAME
    
    # Test and reload Nginx
    echo -e "${GREEN}Testing and reloading Nginx...${NC}"
    sudo nginx -t && sudo systemctl reload nginx
    
    echo -e "${GREEN}Setting up auto-renewal for SSL certificate...${NC}"
    sudo systemctl status certbot.timer
    
    echo -e "${GREEN}SSL setup completed successfully!${NC}"
EOF

echo -e "\n${GREEN}SSL has been set up for $DOMAIN${NC}"
echo "Your application should now be accessible via HTTPS at https://$DOMAIN" 