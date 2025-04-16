"""
Gunicorn configuration file for Backyard Billboards application
"""
import os
import sys

# Port configuration - critical for Replit deployments
try:
    # First try to get the PORT from environment variable (Replit deployment uses this)
    port = int(os.environ.get("PORT", 5000))
    
    # For debugging
    print(f"Using port: {port}", file=sys.stderr)
    
    # Bind to all interfaces
    bind = f"0.0.0.0:{port}"
except Exception as e:
    print(f"Error configuring port: {e}", file=sys.stderr)
    # Default fallback - should work with most setups
    bind = "0.0.0.0:5000"
    print("Falling back to default port 5000", file=sys.stderr)

# Application configuration - DO NOT CHANGE application name
wsgi_app = "wsgi:application"  # This must match wsgi.py

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

# Process naming
proc_name = "backyard-billboards"

# Print configuration for debugging
print(f"Gunicorn configuration: bind={bind}, workers={workers}", file=sys.stderr)