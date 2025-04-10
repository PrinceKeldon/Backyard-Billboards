"""
Gunicorn configuration file for Backyard Billboards application
Used in both development and production environments
"""
import os
import multiprocessing

# Bind to all network interfaces on the specified port
# Use Replit-specific $PORT if available, otherwise default to 5000
port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"

# Set workers based on available CPU cores - optimal for Replit
workers = multiprocessing.cpu_count() * 2 + 1
workers = min(workers, 4)  # Cap at 4 workers maximum for Replit

# Application module - this is the entry point
wsgi_app = "wsgi:application" 

# Configure timeouts (in seconds) - increased for better reliability
timeout = 300  # 5 minutes
keepalive = 60  # 1 minute

# Reuse port (helps with socket issues during restarts)
reuse_port = True

# Use synchronous workers - reliable for Flask
worker_class = "sync"

# Set maximum number of simultaneous requests per worker
worker_connections = 1000

# Maximum requests before worker restart to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging configuration
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"

# Enable auto-reload in development mode
reload = bool(os.environ.get("GUNICORN_RELOAD", False))

# Don't daemonize - important for containerized environments like Replit
daemon = False

# Simplify application startup
preload_app = False

# Graceful shutdown timeout - increased to match main timeout
graceful_timeout = 300