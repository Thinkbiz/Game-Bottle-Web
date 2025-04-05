import multiprocessing
import os

# Worker Settings
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'geventwebsocket.gunicorn.workers.GeventWebSocketWorker'
worker_connections = 1000

# Server Settings
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
keepalive = 30  # Increased for WebSocket connections
graceful_timeout = 120
timeout = 120

# Logging
accesslog = "./logs/access.log"
errorlog = "./logs/error.log"
loglevel = "debug" if os.environ.get('DEBUG') == 'true' else "info"
capture_output = True
enable_stdio_inheritance = True  # Important for WebSocket logging

# Process naming
proc_name = "game_web"

# Server mechanics
daemon = False
pidfile = None  # Don't create PID file in container
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Debug settings
reload = os.environ.get('DEBUG') == 'true'
reload_extra_files = [
    './views/',
    './static/'
]

# Server hooks
def on_starting(server):
    """Log when the server starts."""
    server.log.info("Starting Gunicorn server...")

def on_exit(server):
    """Log when the server exits."""
    server.log.info("Shutting down Gunicorn server...") 