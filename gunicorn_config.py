
"""
Gunicorn configuration file for Backyard Billboards application
"""
import os

# Port configuration - using exactly the format requested
bind = "0.0.0.0:" + str(os.environ.get("PORT", 5000))

# Worker configuration - keep simple for Replit
workers = 1
worker_class = "sync"

# Timeouts
timeout = 120
keepalive = 60

# Logging - stdout/stderr for easy troubleshooting
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Deployment settings
daemon = False
reload = True
