
"""
WSGI entry point for Replit deployment
This is the file that gunicorn uses as its entry point
"""
# Import the Flask application
from app import app

# Create the WSGI application object - this exact variable name is required by Gunicorn
application = app

# This conditional enables direct testing of the WSGI application
if __name__ == "__main__":
    print("WSGI application is available as 'application'")
    print("The application object is:", application)
    # Run the application in development mode if executed directly
    application.run(host="0.0.0.0", port=5000, debug=True)
