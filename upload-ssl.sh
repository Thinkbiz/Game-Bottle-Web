#!/bin/bash
# Script to upload Let's Encrypt SSL certificates to the server

# Configuration
VPS_HOST="gamebottle"  # Use SSH config entry instead of explicit details
DOMAIN="nowmakefunthings.com"
LETSENCRYPT_DIR="./letsencrypt"  # Local directory where Let's Encrypt certificates are stored
REMOTE_CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"
DRY_RUN=false

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Process command line arguments
for arg in "$@"; do
  case $arg in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
  esac
done

echo -e "${YELLOW}=== Let's Encrypt SSL Certificate Upload Script ===${NC}"
if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}DRY RUN MODE: No changes will be made${NC}"
fi
echo "This script will upload your Let's Encrypt SSL certificates to the server."

# Check if Let's Encrypt certificates exist
if [ ! -d "${LETSENCRYPT_DIR}/live/${DOMAIN}" ]; then
    echo -e "${RED}Let's Encrypt certificates for ${DOMAIN} not found in ${LETSENCRYPT_DIR}/live/ directory.${NC}"
    exit 1
fi

# Check for required certificate files
if [ ! -f "${LETSENCRYPT_DIR}/live/${DOMAIN}/fullchain.pem" ] || [ ! -f "${LETSENCRYPT_DIR}/live/${DOMAIN}/privkey.pem" ]; then
    echo -e "${RED}Required certificate files not found in ${LETSENCRYPT_DIR}/live/${DOMAIN}/.${NC}"
    echo "Expected files: fullchain.pem and privkey.pem"
    exit 1
fi

# Create remote directories
echo -e "\n${GREEN}Creating certificate directories on server...${NC}"
if [ "$DRY_RUN" = false ]; then
  ssh $VPS_HOST << EOF
      sudo mkdir -p ${REMOTE_CERT_DIR}
      sudo chmod 755 ${REMOTE_CERT_DIR}
EOF
else
  echo "Would run: ssh $VPS_HOST"
  echo "  sudo mkdir -p ${REMOTE_CERT_DIR}"
  echo "  sudo chmod 755 ${REMOTE_CERT_DIR}"
fi

# Upload certificates
echo -e "\n${GREEN}Uploading SSL certificates to server...${NC}"
if [ "$DRY_RUN" = false ]; then
  scp "${LETSENCRYPT_DIR}/live/${DOMAIN}/fullchain.pem" $VPS_HOST:${REMOTE_CERT_DIR}/
  scp "${LETSENCRYPT_DIR}/live/${DOMAIN}/privkey.pem" $VPS_HOST:${REMOTE_CERT_DIR}/
  scp "${LETSENCRYPT_DIR}/live/${DOMAIN}/cert.pem" $VPS_HOST:${REMOTE_CERT_DIR}/
  scp "${LETSENCRYPT_DIR}/live/${DOMAIN}/chain.pem" $VPS_HOST:${REMOTE_CERT_DIR}/
else
  echo "Would run: scp \"${LETSENCRYPT_DIR}/live/${DOMAIN}/fullchain.pem\" $VPS_HOST:${REMOTE_CERT_DIR}/"
  echo "Would run: scp \"${LETSENCRYPT_DIR}/live/${DOMAIN}/privkey.pem\" $VPS_HOST:${REMOTE_CERT_DIR}/"
  echo "Would run: scp \"${LETSENCRYPT_DIR}/live/${DOMAIN}/cert.pem\" $VPS_HOST:${REMOTE_CERT_DIR}/"
  echo "Would run: scp \"${LETSENCRYPT_DIR}/live/${DOMAIN}/chain.pem\" $VPS_HOST:${REMOTE_CERT_DIR}/"
fi

# Set permissions
echo -e "\n${GREEN}Setting proper permissions...${NC}"
if [ "$DRY_RUN" = false ]; then
  ssh $VPS_HOST << EOF
      sudo chmod 644 ${REMOTE_CERT_DIR}/fullchain.pem
      sudo chmod 640 ${REMOTE_CERT_DIR}/privkey.pem
      sudo chmod 644 ${REMOTE_CERT_DIR}/cert.pem
      sudo chmod 644 ${REMOTE_CERT_DIR}/chain.pem
      
      # Test Nginx configuration
      sudo nginx -t
      
      # If test passes, reload Nginx
      if [ \$? -eq 0 ]; then
          sudo systemctl restart nginx
          echo "SSL certificates uploaded and nginx restarted."
      else
          echo "Nginx configuration test failed. Please check the configuration."
      fi
EOF
else
  echo "Would run: ssh $VPS_HOST"
  echo "  sudo chmod 644 ${REMOTE_CERT_DIR}/fullchain.pem"
  echo "  sudo chmod 640 ${REMOTE_CERT_DIR}/privkey.pem"
  echo "  sudo chmod 644 ${REMOTE_CERT_DIR}/cert.pem"
  echo "  sudo chmod 644 ${REMOTE_CERT_DIR}/chain.pem"
  echo "  sudo nginx -t"
  echo "  sudo systemctl restart nginx"
fi

echo -e "\n${GREEN}SSL certificates uploaded successfully!${NC}"
if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}(This was a dry run, no changes were made)${NC}"
fi
echo "Your application should now be accessible via HTTPS at https://${DOMAIN}" 