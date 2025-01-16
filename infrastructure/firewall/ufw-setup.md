# UFW Firewall Configuration

## Installation
```bash
apt-get install -y ufw
```

## Basic Rules
The following ports are open:
- SSH (22/tcp)
- HTTP (80/tcp)
- HTTPS (443/tcp)

## Setup Commands
```bash
# Enable UFW
ufw enable

# Allow SSH
ufw allow ssh

# Allow HTTP
ufw allow http

# Allow HTTPS
ufw allow https

# Check Status
ufw status
```

## Current Configuration
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443                        ALLOW       Anywhere
22/tcp (v6)               ALLOW       Anywhere (v6)
80/tcp (v6)               ALLOW       Anywhere (v6)
443 (v6)                  ALLOW       Anywhere (v6)
```

## Security Notes
- Only essential ports are open
- IPv6 is configured
- Default deny policy for incoming traffic
- Default allow policy for outgoing traffic 