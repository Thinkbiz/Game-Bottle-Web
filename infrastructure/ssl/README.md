# SSL Configuration

This directory contains documentation for the SSL setup on our VPS.

## Current Configuration

- Domain: nowmakefunthings.com
- SSL Provider: Let's Encrypt
- Certificate Location: /etc/letsencrypt/live/nowmakefunthings.com/
- Auto-renewal: Enabled via Certbot

## Certificate Files

- `fullchain.pem`: Full certificate chain
- `privkey.pem`: Private key
- `cert.pem`: Domain certificate
- `chain.pem`: CA chain certificates

## Renewal Information

Certbot automatically manages renewal via a cron job. Certificates are valid for 90 days and auto-renew 30 days before expiration.

To manually renew:
```bash
certbot renew
```

To check certificate status:
```bash
certbot certificates
```

## Initial Setup Commands

```bash
# Install Certbot and Nginx plugin
apt install certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d nowmakefunthings.com

# Verify auto-renewal
systemctl status certbot.timer
```

## Security Notes

- Private keys are stored in `/etc/letsencrypt/live/nowmakefunthings.com/`
- Only root has access to the certificate files
- HTTPS redirect is enforced for all traffic
- HSTS is enabled with a max-age of 31536000 seconds (1 year) 