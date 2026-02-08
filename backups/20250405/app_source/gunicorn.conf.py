import multiprocessing

# Gunicorn configuration file for Game-Bottle-Web

# Bind to localhost on port 8000
bind = "127.0.0.1:8000"

# Number of worker processes
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = "sync"

# Timeout in seconds
timeout = 120

# Log settings
accesslog = "/app/logs/gunicorn-access.log"
errorlog = "/app/logs/gunicorn-error.log"
loglevel = "info"

# Process name
proc_name = "game-bottle-web"

# Preload application code before forking workers
preload_app = True

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Daemon mode
daemon = False  # We'll use systemd to manage the process

# SSL is handled by Nginx, so we don't need it here 