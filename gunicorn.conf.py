import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 1
worker_class = "sync"
threads = 2
worker_connections = 1000
max_requests = 0
timeout = 120
keepalive = 30

# Logging
errorlog = "/app/logs/gunicorn-error.log"
accesslog = "/app/logs/gunicorn-access.log"
loglevel = "debug"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
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
    server.log.info("Starting Gunicorn server...")

def on_exit(server):
    server.log.info("Shutting down Gunicorn server...") 