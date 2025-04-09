import os

# Bind to all network interfaces on the specified port
bind = "0.0.0.0:" + os.environ.get("PORT", "5000")

# Number of worker processes for handling requests
workers = 4

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Timeout in seconds
timeout = 30

# Reuse port (helps with socket issues during restarts)
reuse_port = True

# Enable debugging logs
loglevel = "info"

# Enable auto-reload on file changes (development only)
reload = True

# Preload application to improve startup time
preload_app = True