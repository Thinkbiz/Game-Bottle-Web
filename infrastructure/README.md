# Infrastructure Configuration

This directory contains all infrastructure-related configurations and documentation for the Monsters and Treasure game.

## Directory Structure
- `nginx/` - Nginx configuration files and setup instructions
- `ssl/` - SSL certificate setup and renewal instructions
- `firewall/` - UFW firewall rules and security configurations

## Server Setup
- VPS IP: 167.88.39.165
- Domain: nowmakefunthings.com
- OS: Ubuntu 24.04.1 LTS

## Installed Components
1. **Nginx**
   - Reverse proxy
   - Rate limiting
   - Security headers
   - Static file serving

2. **UFW Firewall**
   - Port 22 (SSH)
   - Port 80 (HTTP)
   - Port 443 (HTTPS)

3. **SSL/TLS**
   - Let's Encrypt certificates
   - Auto-renewal setup

## Deployment Instructions
1. Clone this repository
2. Follow setup instructions in each component's directory
3. Use docker-compose for application deployment

## Maintenance
- SSL certificates auto-renew every 90 days
- Log rotation is configured for all services
- Regular security updates should be applied 