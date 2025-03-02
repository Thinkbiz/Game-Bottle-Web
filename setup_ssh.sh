#!/bin/bash

# Configuration
VPS_USER="root"
VPS_HOST="167.88.39.165"
SSH_PASSWORD="X/Nqw3PWHoXgT0g5o"
COMMON_SSH_PORTS=(22 2222 22022 222 2022 2202 220 10022 20022 40022 43022 9922)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Setting up SSH key authentication ===${NC}"

# Check if SSH key exists
if [ ! -f ~/.ssh/id_ed25519.pub ]; then
    echo -e "${RED}SSH key not found. Creating one...${NC}"
    ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
fi

# Find which port SSH is running on
echo -e "${YELLOW}Checking for SSH on common ports...${NC}"
for PORT in "${COMMON_SSH_PORTS[@]}"; do
    echo -e "Trying port $PORT..."
    if nc -z -w 3 $VPS_HOST $PORT 2>/dev/null; then
        echo -e "${GREEN}Found SSH service on port $PORT!${NC}"
        SSH_PORT=$PORT
        break
    fi
done

if [ -z "$SSH_PORT" ]; then
    echo -e "${RED}Could not find SSH service on any common port.${NC}"
    echo "Please check with your VPS provider for the correct SSH access details."
    exit 1
fi

# Update our deployment scripts with the correct port
echo -e "${YELLOW}Updating deployment scripts with port $SSH_PORT...${NC}"
sed -i '' "s/VPS_PORT=\"22\"/VPS_PORT=\"$SSH_PORT\"/" deploy.sh
sed -i '' "s/VPS_PORT=\"22\"/VPS_PORT=\"$SSH_PORT\"/" backup.sh
sed -i '' "s/VPS_PORT=\"22\"/VPS_PORT=\"$SSH_PORT\"/" setup-ssl.sh

# First create the .ssh directory on the server if it doesn't exist
echo -e "${YELLOW}Creating .ssh directory on server...${NC}"
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -p $SSH_PORT $VPS_USER@$VPS_HOST "mkdir -p ~/.ssh && chmod 700 ~/.ssh"

# Copy the public key to the server's authorized_keys file
echo -e "${YELLOW}Copying SSH public key to server...${NC}"
sshpass -p "$SSH_PASSWORD" cat ~/.ssh/id_ed25519.pub | ssh -o StrictHostKeyChecking=no -p $SSH_PORT $VPS_USER@$VPS_HOST "cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

# Test connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
ssh -o StrictHostKeyChecking=no -p $SSH_PORT $VPS_USER@$VPS_HOST "echo SSH connection successful && uname -a"

echo -e "\n${GREEN}SSH key authentication set up successfully!${NC}"
echo "Now you can proceed with deployment without entering the password." 