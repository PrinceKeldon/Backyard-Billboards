"""
Gunicorn configuration file for Backyard Billboards application
"""
import os

# Always use the environment's PORT variable (required for deployment)
port = int(os.environ.get("PORT", 5000))
bind = f"0.0.0.0:{port}"

# Set appropriate worker count for Replit
workers = 2

# Use standard synchronous workers
worker_class = "sync"

# Timeouts
timeout = 120
keepalive = 60

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Simple configuration
daemon = False
reload = True