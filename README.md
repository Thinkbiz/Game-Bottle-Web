# Monsters and Treasure Game

A web-based adventure game built with Python and Bottle.

Deployment test timestamp: 2024-02-15

## Local Development

1. Clone the repository:

# Game-Bottle-Web Production Branch

This is the production branch of the Game-Bottle-Web project. This branch contains the code and configurations that are deployed to the VPS.

## Branch Structure

- `main`: Development branch, contains the latest features and changes
- `production`: Production branch, contains the stable code deployed to VPS

## Deployment Process

1. All new features and changes should be developed in `main` branch
2. When ready to deploy:
   ```bash
   # Update main branch
   git checkout main
   git pull origin main

   # Merge changes into production
   git checkout production
   git merge main

   # Push to production
   git push origin production
   ```

3. Deploy to VPS:
   ```bash
   # SSH into VPS
   ssh user@your-vps

   # Pull latest production code
   cd /path/to/game
   git pull origin production

   # Restart services
   sudo systemctl restart game-web
   ```

## Configuration Differences

The production branch contains specific configurations for the VPS environment:

1. Gunicorn settings in `gunicorn.conf.py`:
   - Worker class: gevent
   - Number of workers: 4
   - Log paths: /var/log/game-web/
   - Enhanced logging format

2. Application settings:
   - Enhanced state logging
   - Production-specific paths
   - Debug mode disabled

## Monitoring

- Application logs: `/var/log/game-web/`
- Game state logs: `/var/log/game-web/game_state.log`
- Gunicorn logs: 
  - Access: `/var/log/game-web/gunicorn-access.log`
  - Error: `/var/log/game-web/gunicorn-error.log`

## Rollback Process

If issues are found in production:

1. Identify the last working commit
   ```bash
   git log --oneline
   ```

2. Rollback to that commit
   ```bash
   git checkout production
   git reset --hard <commit-hash>
   git push -f origin production
   ```

3. Deploy the rollback
   ```bash
   # On VPS
   git pull origin production
   sudo systemctl restart game-web
   ```