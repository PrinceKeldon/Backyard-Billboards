"""
Gunicorn configuration file
"""
import os
import multiprocessing

# Use PORT environment variable or default to 5000
port = int(os.environ.get("PORT", 5000))
bind = f"0.0.0.0:{port}"

# Worker configuration
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 300
keepalive = 60

# Access logging
accesslog = "-"
errorlog = "-"
loglevel = "info"