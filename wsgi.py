"""
WSGI application entry point for Happy Hour Hub
This file serves as the main module for deployment
"""
# Import the Flask application directly from app.py
from app import app as application

# This allows the file to be run directly for development
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    application.run(host="0.0.0.0", port=port, debug=True)