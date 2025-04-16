
"""
WSGI entry point for Replit deployment
This is the file that gunicorn uses as its entry point
"""
# Import the Flask application
from app import app

# Create the WSGI application object
application = app

# This helps debug WSGI issues
if __name__ == "__main__":
    print("WSGI application is available as 'application'")
    print("The application object is:", application)
