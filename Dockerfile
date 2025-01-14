FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=1 \
    TIMEOUT=120 \
    KEEP_ALIVE=30

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs && \
    chmod 777 /app/data /app/logs

# Volume for persistent data and logs
VOLUME ["/app/data", "/app/logs"]

# Expose the port
EXPOSE 8000

# Use tini as init system
ENTRYPOINT ["/usr/bin/tini", "--"]

# Run the application with gunicorn
CMD ["gunicorn", "--config", "/app/gunicorn.conf.py", "--preload", "web_game:app"] 