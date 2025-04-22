"""
WSGI application entry point for Backyard Billboards
This file serves as the main module for Replit deployment
"""
# Import the Flask application directly from app.py
from app import app

# Create a reference to the application for wsgi compatibility
application = app

# This allows the file to be run directly for development
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
