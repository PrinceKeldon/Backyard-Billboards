"""
Gunicorn configuration file for Backyard Billboards application
"""
import os
import multiprocessing

# For deployment: Use PORT environment variable
# For local development: Use 5000 as the default
port = int(os.environ.get("PORT", 5000))
bind = f"0.0.0.0:{port}"

# Set workers based on CPU cores, but cap at 4 workers for Replit
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)

# Use synchronous workers
worker_class = "sync"

# Configure timeouts and connections
timeout = 300
keepalive = 60
worker_connections = 1000

# Enable port reuse
reuse_port = True

# Restart workers periodically to free resources
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Development mode auto-reload
reload = True

# Process management
daemon = False
preload_app = False
graceful_timeout = 30