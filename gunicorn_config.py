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

# Use 4 workers as specified in deployment
workers = 4

# Application module - this is the entry point
wsgi_app = "wsgi:application" 

# Configure timeouts (in seconds)
timeout = 120
keepalive = 5

# Reuse port (helps with socket issues during restarts)
reuse_port = True

# Use synchronous workers
worker_class = "sync"

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

# Graceful shutdown timeout
graceful_timeout = 30