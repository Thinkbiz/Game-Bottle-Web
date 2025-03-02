# Monsters and Treasure Game

A web-based adventure game built with Python and Bottle, featuring Docker containerization for consistent development and deployment.

Deployment test timestamp: 2024-02-15

## Branch Structure

- `main`: Production-ready code that has been tested and verified
- `development`: Active development branch for ongoing work
- `feature/*`: Feature-specific branches for new functionality

## Local Development

### Standard Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Game-Bottle-Web
```

2. Set up a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Run the application:
```bash
python web_game.py
```

### Docker Development

1. Build and start the Docker container:
```bash
docker-compose up -d
```

2. Access the application at http://localhost:8000

## Deployment

The application is containerized for deployment to ensure consistency between development and production environments.

### Deployment Process

1. Develop and test locally using Docker to match production environment
2. Merge completed features into the `development` branch
3. Test thoroughly on the development branch
4. When ready for production, merge into `main`
5. Deploy to VPS using the deployment script:
```bash
./deploy-container.sh
```

### Maintaining Consistency

To ensure consistency between local and VPS environments:

1. Always use Docker for development to match production environment
2. Use Git for code synchronization between environments
3. Database changes should be scripted and versioned
4. Use the provided backup scripts to preserve data:
```bash
./backup.sh
```

For full deployment details, see [DEPLOYMENT.md](DEPLOYMENT.md).

## VPS Environment

The production deployment uses:
- Nginx as a reverse proxy
- Docker for containerization
- Let's Encrypt for SSL certificates
- Systemd for service management

## Troubleshooting

Common issues and their solutions can be found in the [MIGRATION-GUIDE.md](MIGRATION-GUIDE.md) file.