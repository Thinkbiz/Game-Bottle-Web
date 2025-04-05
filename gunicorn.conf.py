import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
backlog = 2048

# Worker processes - optimized for single CPU
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'geventwebsocket.gunicorn.workers.GeventWebSocketWorker'
worker_connections = 1000
threads = 4  # More threads since we're using fewer workers
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 2

# Logging
errorlog = "./logs/error.log"
accesslog = "./logs/access.log"
loglevel = "debug" if os.environ.get('DEBUG') == 'true' else "info"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
capture_output = True

# Process naming
proc_name = "game_web"

# Server mechanics
daemon = False
pidfile = "/app/logs/gunicorn.pid"
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

# Server hooks
def on_starting(server):
    """Log when the server starts."""
    server.log.info("Starting Gunicorn server...")

def on_exit(server):
    """Log when the server exits."""
    server.log.info("Shutting down Gunicorn server...") 