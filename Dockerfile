FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Create data directory for SQLite database
RUN mkdir -p /app/data && \
    chmod 777 /app/data

# Volume for persistent data
VOLUME ["/app/data"]

# Expose the port
EXPOSE 8000

# Run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "web_game:app"] 