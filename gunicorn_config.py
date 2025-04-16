
"""
Gunicorn configuration file for Backyard Billboards application
"""
import os
import multiprocessing

# Always bind to port 5000 to match port forwarding configuration
bind = "0.0.0.0:5000"

# Set workers based on CPU cores
workers = multiprocessing.cpu_count() * 2 + 1
workers = min(workers, 4)  # Cap at 4 workers for Replit

# Configure timeouts
timeout = 300
keepalive = 60

# Enable port reuse
reuse_port = True

# Use synchronous workers
worker_class = "sync"

# Worker connections
worker_connections = 1000

# Restart workers periodically
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Development mode auto-reload
reload = bool(os.environ.get("GUNICORN_RELOAD", False))

# Process management
daemon = False
preload_app = False
graceful_timeout = 300
