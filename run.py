"""
Unified entry point for Backyard Billboards
This file provides a consistent way to run the application in any environment
"""
# Direct import from app.py
from app import app

# This is used when running this file directly
if __name__ == "__main__":
    # Run the Flask application directly
    app.run(host="0.0.0.0", port=5000, debug=True)