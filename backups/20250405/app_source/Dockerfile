FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEVELOPMENT=0

# Make entry scripts executable
RUN chmod +x ./scripts/*.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=5s \
  CMD curl -f http://localhost:8000/health || exit 1

# Run with Gunicorn for production
CMD ["gunicorn", "--workers=4", "--bind", "0.0.0.0:8000", "web_game:app"] 