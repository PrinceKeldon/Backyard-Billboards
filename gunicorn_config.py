
"""
Gunicorn configuration file for Backyard Billboards application
"""
import os

# Port configuration - using PORT env variable for autoscaling
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"

# Worker configuration
workers = 1
threads = 2
worker_class = "sync"

# Timeouts
timeout = 300
graceful_timeout = 120
keepalive = 60

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Deployment settings
daemon = False
reload = False
preload_app = False

# Application specific settings
forwarded_allow_ips = "*"
