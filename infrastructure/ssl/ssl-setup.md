# SSL Configuration with Let's Encrypt

## Domain Information
- Domain: nowmakefunthings.com
- Server IP: 167.88.39.165

## Installation
```bash
# Install Certbot and Nginx plugin
apt-get update
apt-get install -y certbot python3-certbot-nginx
```

## Certificate Generation
```bash
# Generate certificate
certbot --nginx -d nowmakefunthings.com
```

## Auto-renewal
Certbot automatically creates a renewal timer. To test the renewal process:
```bash
certbot renew --dry-run
```

## Certificate Location
- Certificate: /etc/letsencrypt/live/nowmakefunthings.com/fullchain.pem
- Private Key: /etc/letsencrypt/live/nowmakefunthings.com/privkey.pem

## Renewal Schedule
- Certificates are valid for 90 days
- Automatic renewal occurs twice daily when certificates are close to expiration
- Nginx is automatically reloaded after renewal

## Manual Renewal
```bash
certbot renew
``` 