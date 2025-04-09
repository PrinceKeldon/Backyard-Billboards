"""
WSGI entry point for Replit deployment
"""

# Import the Flask app
from main import app as application

# This is for WSGI compliance - Flask app must be named "application"
# in the WSGI entry point file
if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000)