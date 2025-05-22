
"""
Gunicorn configuration file for Backyard Billboards application
"""
import os
import multiprocessing

# Port configuration - using exactly the format requested 
# This is critical for deployment - must use PORT env variable
bind = "0.0.0.0:" + str(os.environ.get("PORT", 5000))

# Worker configuration - simple and reliable for Replit
workers = 1
threads = 2
worker_class = "sync"

# Timeouts - more generous for application startup
timeout = 300
graceful_timeout = 120
keepalive = 60

# Logging - stdout/stderr for easy troubleshooting
accesslog = "-"
errorlog = "-"
loglevel = "debug"  # Increased log level for deployment troubleshooting

# Deployment settings
daemon = False
reload = False  # Disable reload in production
preload_app = False  # Don't preload for better error handling

# Application specific settings
forwarded_allow_ips = "*"  # Important for proxy settings
