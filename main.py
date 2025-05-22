"""
Main entry point for Happy Hour Hub
This file allows direct execution for development and testing
"""
# Import the Flask application directly from app.py
from app import app

# This allows the file to be run directly for development
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
