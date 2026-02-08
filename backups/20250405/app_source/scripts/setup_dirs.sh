#!/bin/bash
# Setup directories required by the application

# Make script exit on first error
set -e

echo "Creating required directories..."

# Create data directory
mkdir -p data
echo "- Created data directory"

# Create logs directory 
mkdir -p logs
echo "- Created logs directory"

# Create empty log files if they don't exist
touch logs/app.log
touch logs/gunicorn-access.log
touch logs/gunicorn-error.log
echo "- Created log files"

# Set proper permissions
chmod -R 755 data logs
echo "- Set directory permissions"

# Create .gitkeep files
touch data/.gitkeep
touch logs/.gitkeep
echo "- Created .gitkeep files"

echo "Directory setup completed successfully!" 