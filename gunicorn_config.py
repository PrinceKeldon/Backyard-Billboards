
"""
Gunicorn configuration file for Backyard Billboards application
"""
import os
import multiprocessing

# Worker configuration - optimized for Replit deployment
workers = 1  
threads = 2
worker_class = "sync"

# Timeouts - adjusted for application startup
timeout = 60
graceful_timeout = 30
keepalive = 5

# Logging configuration
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Bind to PORT environment variable
# Default to port 5000 for consistency
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# Production settings
daemon = False
reload = False
preload_app = True
forwarded_allow_ips = "*"
