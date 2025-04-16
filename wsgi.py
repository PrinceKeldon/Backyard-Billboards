
"""
WSGI entry point for Replit deployment
This is the file that gunicorn uses as its entry point
"""
from app import app

# Expose the Flask app as 'application' for WSGI standard
application = app
