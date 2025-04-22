"""
WSGI application entry point for Backyard Billboards
This file serves as the main module for Replit deployment
"""
# Simply import the application from wsgi.py
from wsgi import application

# This allows the file to be run directly for development
if __name__ == "__main__":
    application.run(host="0.0.0.0", port=8000, debug=True)
