
"""
Gunicorn configuration file for Backyard Billboards application
"""
import os

# Port configuration for production deployment
bind = "0.0.0.0:5000"

# Worker configuration - keep simple for Replit
workers = 1
worker_class = "sync"

# Timeouts
timeout = 120
keepalive = 60

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Deployment settings
daemon = False
reload = False  # Disable reload in production
