"""
Development entry point for Backyard Billboards
"""
# Direct import from app.py for development
from app import app
import os

# This is only used when running this file directly for development
if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5000))
    
    # Run the app for development
    app.run(host="0.0.0.0", port=port, debug=True)
