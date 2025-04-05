import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes - optimized for single CPU
workers = 2  # 2-3 per core, we have 1 core
worker_class = "gevent"
worker_connections = 1000
threads = 4  # More threads since we're using fewer workers
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 5

# Logging
errorlog = "/app/logs/gunicorn-error.log"
accesslog = "/app/logs/gunicorn-access.log"
loglevel = "info"
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

# Server hooks
def on_starting(server):
    """Log when the server starts."""
    server.log.info("Starting Gunicorn server...")

def on_exit(server):
    """Log when the server exits."""
    server.log.info("Shutting down Gunicorn server...") 