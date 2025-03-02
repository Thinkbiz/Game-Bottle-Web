import multiprocessing
import os
import importlib.util

# Gunicorn configuration file for Game-Bottle-Web

# Check if gevent is available
gevent_available = importlib.util.find_spec("gevent") is not None

# Bind to all interfaces on port 8000
bind = "0.0.0.0:8000"

# Adjust worker count based on available resources
# For smaller VPS instances, you might want to limit this
workers = min(multiprocessing.cpu_count() * 2 + 1, 6)  # Cap at 6 workers max

# Worker class - gevent is better for I/O bound applications
# Fall back to sync worker if gevent is not available
worker_class = "gevent" if gevent_available else "sync"

# Worker settings
worker_connections = 1000
timeout = 60
keepalive = 5
threads = 2

# Log settings
accesslog = "/app/logs/gunicorn-access.log"
errorlog = "/app/logs/gunicorn-error.log"
loglevel = "info"
access_log_format = '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Performance tuning
max_requests = 1000
max_requests_jitter = 50
graceful_timeout = 30
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Process name
proc_name = "game-bottle-web"

# Preload application code before forking workers
preload_app = True

# Handle SIGTERM correctly
forwarded_allow_ips = '*'

# Daemon mode
daemon = False  # We'll use systemd to manage the process

# SSL is handled by Nginx, so we don't need it here

def on_starting(server):
    """
    Log when server starts
    """
    server.log.info("Starting Gunicorn server for Game-Bottle-Web")
    if not gevent_available:
        server.log.warning("gevent not available, using sync worker class")

def on_reload(server):
    """
    Log when server reloads
    """
    server.log.info("Reloading Gunicorn server for Game-Bottle-Web")

def post_fork(server, worker):
    """
    Set process group for worker
    """
    server.log.info(f"Worker spawned (pid: {worker.pid})")
    
def worker_exit(server, worker):
    """
    Handle worker exit
    """
    server.log.info(f"Worker exited (pid: {worker.pid})") 