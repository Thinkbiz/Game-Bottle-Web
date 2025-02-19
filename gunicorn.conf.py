# Logging
errorlog = "logs/gunicorn-error.log"
accesslog = "logs/gunicorn-access.log"
loglevel = "debug"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
capture_output = True

# Process naming
proc_name = "game_web"

# Server mechanics
daemon = False
pidfile = "logs/gunicorn.pid"

# Server socket
bind = "127.0.0.1:8000"
workers = 4 