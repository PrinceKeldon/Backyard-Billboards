
"""
WSGI entry point for Replit deployment
This is the file that gunicorn uses as its entry point
"""
# Import the Flask application from app.py
from app import app

# Create the WSGI application object - this name is required by Gunicorn
application = app

# For direct execution during development
if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000, debug=True)
