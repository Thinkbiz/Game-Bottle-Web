# Game-Bottle-Web Deployment Guide

This guide provides step-by-step instructions for deploying the Game-Bottle-Web application to a production server.

## Prerequisites

- A VPS running Ubuntu 20.04 or later
- Domain name (nowmakefunthings.com) pointing to your VPS
- SSH access to your VPS
- SSH key pair on your local machine

## Deployment Steps

### 1. Prepare Your Local Environment

Clone the repository and navigate to the project directory:

```bash
git clone <repository-url>
cd Game-Bottle-Web
```

### 2. Configure SSH Access

Set up your SSH configuration for easier access:

```bash
# Generate a new SSH key if you don't have one
ssh-keygen -t ed25519 -f ~/.ssh/vps_key -C "VPS Access Key" -N ""

# Copy the key to the server (you'll need to enter your password once)
ssh-copy-id -i ~/.ssh/vps_key.pub root@167.88.39.165

# Add an SSH config entry
echo -e "\n# Game Bottle Web VPS\nHost gamebottle\n    HostName 167.88.39.165\n    User root\n    IdentityFile ~/.ssh/vps_key\n    IdentitiesOnly yes" >> ~/.ssh/config

# Test the connection
ssh gamebottle echo "Connection successful"
```

### 3. Prepare SSL Certificates

Ensure your Let's Encrypt certificates are in the correct directory:

```bash
ls -la ./letsencrypt/live/nowmakefunthings.com/
```

You should see files like `fullchain.pem` and `privkey.pem` in this directory.

### 4. Initial Deployment

Run the deployment script:

```bash
chmod +x deploy.sh
./deploy.sh
```

This script will:
- Copy your code to the server
- Install dependencies
- Set up Nginx
- Configure a systemd service for your application
- Create SSL certificate directories

### 5. Upload SSL Certificates

After the initial deployment, upload your SSL certificates:

```bash
chmod +x upload-ssl.sh
./upload-ssl.sh
```

You can also perform a dry run first to see what changes will be made:

```bash
./upload-ssl.sh --dry-run
```

This will:
- Copy your SSL certificates to the correct locations on the server
- Set appropriate permissions
- Restart Nginx to apply SSL configuration

## Maintenance Tasks

### Restarting the Application

```bash
ssh gamebottle 'sudo systemctl restart game-bottle-web'
```

### Viewing Logs

```bash
ssh gamebottle 'sudo journalctl -u game-bottle-web'
```

### Updating the Application

Run the deployment script again:

```bash
./deploy.sh
```

## Troubleshooting

### Checking Application Status

```bash
ssh gamebottle 'sudo systemctl status game-bottle-web'
```

### Checking Nginx Status

```bash
ssh gamebottle 'sudo systemctl status nginx'
```

### Checking Nginx Configuration

```bash
ssh gamebottle 'sudo nginx -t'
```

### Checking SSL Certificate

```bash
ssh gamebottle 'openssl x509 -in /etc/letsencrypt/live/nowmakefunthings.com/fullchain.pem -text -noout'
``` 