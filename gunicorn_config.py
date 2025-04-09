import os
import multiprocessing

# Bind to all network interfaces on the specified port
# Use Replit-specific $PORT if available, otherwise default to 5000
bind = "0.0.0.0:" + os.environ.get("PORT", "5000")

# Use 4 workers as specified in deployment
workers = 4

# Configure timeouts (in seconds)
timeout = 120
keepalive = 5

# Use synchronous workers
worker_class = "sync"

# Logging configuration
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Disable development settings
reload = False

# Don't daemonize - important for containerized environments like Replit
daemon = False

# Simplify application startup
preload_app = False  # Changed to avoid complexity during initialization

# Graceful shutdown timeout
graceful_timeout = 30