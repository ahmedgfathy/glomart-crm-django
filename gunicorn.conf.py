# Gunicorn configuration file for Glomart CRM

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "info"
accesslog = "/var/www/glomart-crm/logs/gunicorn-access.log"
errorlog = "/var/www/glomart-crm/logs/gunicorn-error.log"

# Process naming
proc_name = "glomart-crm"

# User and group
user = "django-user"
group = "django-user"

# Application directory
chdir = "/var/www/glomart-crm"

# Enable preloading the application in master process
preload_app = True

# Disable access logging to stdout (we have accesslog)
disable_redirect_access_to_syslog = True

# SSL (if needed later)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"