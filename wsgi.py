
"""
WSGI entry point for Replit deployment
This is the file that gunicorn uses as its entry point
"""
from app import app

# Keep both names for compatibility
# - 'app' is imported from app.py
# - 'application' is used by some WSGI servers
application = app
