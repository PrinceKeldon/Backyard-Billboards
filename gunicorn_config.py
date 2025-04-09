import os
import multiprocessing

# Bind to all network interfaces on the specified port
# Use Replit-specific $PORT if available, otherwise default to 5000
bind = "0.0.0.0:" + os.environ.get("PORT", "5000")

# Adjust workers based on machine's CPU cores - for Replit, keep it small
workers = min(multiprocessing.cpu_count(), 2)

# Restart workers after this many requests (to prevent memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Configure timeouts (in seconds)
timeout = 120  # Increased for potentially slow operations
keepalive = 5

# Reuse port (helps with socket issues during restarts)
reuse_port = True

# Use both synchronous and asynchronous workers
worker_class = "sync"

# Logging configuration
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"

# Enable auto-reload for development in Replit
reload = True

# Don't daemonize - important for containerized environments like Replit
daemon = False

# Simplify application startup
preload_app = False  # Changed to avoid complexity during initialization

# Graceful shutdown timeout
graceful_timeout = 30