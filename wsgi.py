"""
WSGI entry point for Replit deployment
This is the file that gunicorn uses as its entry point
"""
# The Flask application is defined in app.py
# Just import and rename the app to "application" for WSGI standard
from app import app as application

# That's it! No additional initialization needed