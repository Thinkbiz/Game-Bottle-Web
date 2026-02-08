Description: Rules for Docker container setup on a modest VPS (1 CPU, 4GB RAM)
Globs: Dockerfile, docker-compose*.yml
Content:
- Use 'python:3.11-slim' as the base image for minimal size and low memory usage.
- Implement multi-stage builds to keep runtime images under 100MB where possible.
- Expose port 8000 for Bottle (matches your PORT=8000 default).
- Include a HEALTHCHECK hitting /health (e.g., curl http://localhost:8000/health).
- Optimize for VPS: avoid large dependencies, use --no-cache-dir for pip, keep layer count low.
- Set WORKDIR to /app and run as a non-root user (e.g., USER appuser).
- Mount logs/ and game.db as volumes in docker-compose.yml.
- Document each step with comments explaining each instruction and how it works with the rest of the application. 

