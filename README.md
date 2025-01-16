# Monsters and Treasure Game

A web-based adventure game built with Python and Bottle.

## Local Development

1. Clone the repository:
```bash
git clone https://github.com/Thinkbiz/Game-Bottle-Web.git
cd Game-Bottle-Web
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the development server:
```bash
python web_game.py
```

## Docker Deployment

1. Build and run with Docker Compose:
```bash
docker-compose up -d
```

## Production Deployment

1. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
# Edit .env with your settings
```

2. Use docker-compose.prod.yml:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. Follow infrastructure setup in `/infrastructure` directory:
- Nginx configuration
- SSL certificates
- Firewall rules

## Infrastructure

See `/infrastructure` directory for:
- Server configuration
- Security setup
- Maintenance procedures

## Directory Structure
```
.
├── data/           # Database storage
├── infrastructure/ # Server configuration
├── logs/          # Application logs
├── static/        # Static files
├── views/         # HTML templates
└── docker/        # Docker configuration
```

## Security
- HTTPS enabled
- Rate limiting
- Firewall protection
- Security headers

## Maintenance
- SSL auto-renewal
- Log rotation
- Database backups
- Security updates 